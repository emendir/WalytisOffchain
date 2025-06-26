import multi_crypt
from threading import Thread
from datetime import datetime
import threading
from time import sleep
import json
from walytis_beta_embedded import ipfs
from walytis_identities.did_manager_with_supers import DidManagerWithSupers
from walytis_identities.did_manager_blocks import MemberJoiningBlock
from typing import Callable
from .log import logger_waloff as logger
import walytis_beta_api
from walytis_beta_embedded import ipfs

from walytis_identities.did_manager import DidManager
from walytis_identities.group_did_manager import GroupDidManager
from walytis_beta_api import decode_short_id
from walytis_beta_api._experimental.generic_blockchain import GenericBlock, GenericBlockchain
from walytis_identities.did_manager import blockchain_id_from_did
from . import blockstore
from .data_block import DataBlock, DataBlocksList
COMMS_TIMEOUT_S = 30
MIN_BLOCK_AGE_S = 5


class PrivateBlockchain(blockstore.BlockStore, GenericBlockchain):
    block_received_handler: Callable[[GenericBlock], None] | None = None

    def __init__(
        self,
        group_blockchain: GroupDidManager,
        base_blockchain: GenericBlockchain | None = None,
        block_received_handler: Callable[[GenericBlock], None] | None = None,
        virtual_layer_name: str = "PrivateBlockchain",
        other_blocks_handler: Callable[[GenericBlock], None] | None = None,
        appdata_dir: str = "",
        auto_load_missed_blocks: bool = True,
        forget_appdata: bool = False,
        sequential_block_handling: bool = True,
        update_blockids_before_handling: bool = False,

    ):
        """Initialise a PrivateBlockchain object.

        Args:
            group_blockchain: the object for managing this blockchain's
                participants
            base_blockchain: the blockchain to be used for registering the
                PrivateBlocks (actual content is off-chain).
                If `None`, `group_blockchain.blockchain`
                is used instead.
            block_received_handler: eventhandler to be called when a new
                PrivateBlock is received
            virtual_layer_name: block-topic to identify blocks created by this
                PrivateBlockchain among blocks created without it
            other_blocks_handler: eventhandler to be called when blocks not
                created by this PrivateBlockchain are received
            appdata_dir:
            auto_load_missed_blocks:
            forget_appdata:
            sequential_block_handling:
            update_blockids_before_handling:
        """
        self._terminate = False
        blockstore.BlockStore.__init__(self)
        self.group_blockchain = group_blockchain

        if base_blockchain:
            self.base_blockchain = base_blockchain
        else:
            self.base_blockchain = self.group_blockchain
        self.base_blockchain.block_received_handler = self._on_block_received

        self.virtual_layer_name = virtual_layer_name
        # logger.info(f"PB: Initialising Private Blockchain: {virtual_layer_name}")

        self.init_blockstore()  # RocksDB
        self._init_blocks()  # BlocksLazilyLoaded

        self.block_received_handler = block_received_handler
        self.other_blocks_handler = other_blocks_handler
        if not virtual_layer_name:
            raise ValueError(
                "`virtual_layer_name` cannot be empty!"
            )
        self.content_request_listener = ipfs.listen_for_conversations(
            listener_name=f"PrivateBlocks{self.base_blockchain.blockchain_id}",
            eventhandler=self.handle_content_request
        )

        self.base_blockchain.block_received_handler = self._on_block_received
        # list to store members' DidManagers in
        self.members = {
            self.group_blockchain.member_did_manager.did: self.group_blockchain.member_did_manager
        }
        self._blocks_to_find_thr = Thread(target=self._find_blocks)
        if auto_load_missed_blocks:
            self.load_missed_blocks()
            self._blocks_to_find_thr.start()

    def _init_blocks(self):
        known_block_ids = self.get_known_blocks()

        known_blocks = []
        blocks_to_find = []
        for block in self.base_blockchain.get_blocks():
            if self.virtual_layer_name in block.topics:
                if bytes(block.long_id) in known_block_ids:
                    known_blocks.append(block)
                else:
                    blocks_to_find.append(block)
        self._blocks_to_find = blocks_to_find
        self._blocks = DataBlocksList.from_blocks(
            known_blocks, self, DataBlock)

    def load_missed_blocks(self):
        self.base_blockchain.load_missed_blocks()

    def _find_blocks(self):
        while not self._terminate:
            found_blocks = []
            for block in self._blocks_to_find:
                if self._terminate:
                    return
                private_content = self.ask_around_for_content(block)
                if private_content:
                    found_blocks.append(block)
                    self._on_private_block_received(block, private_content)

            for block in found_blocks:
                self._blocks_to_find.remove(block)

    def load_block(self, block: bytes | GenericBlock) -> DataBlock:
        if isinstance(block, bytes | bytearray):
            block = self.base_blockchain.get_block(block)
        content = self.get_block_content(block.long_id)
        author = self.get_block_author_did(block)
        return DataBlock(block, content, author)

    def get_block_author_did(self, block: DataBlock) -> str:
        i = block.content.index(bytearray([0]))
        author_did = block.content[:i].decode()
        return author_did

    def get_block(self, block_id: bytearray | bytes | int) -> DataBlock:
        if isinstance(block_id, int):
            block_id = self.get_block_ids()[block_id]
        elif isinstance(block_id, bytearray):
            block_id = bytes(block_id)
        return self._blocks.get_block(block_id)

    def get_num_blocks(self) -> int:
        return len(self._blocks)

    def get_blocks(self) -> list[DataBlock]:
        return self._blocks.get_blocks()

    def get_block_ids(self) -> list[bytes]:
        return self._blocks.get_long_ids()

    def add_block(
        self, content: bytes, topics: str | list[str] = []
    ) -> DataBlock:
        sleep(1)

        if isinstance(topics, str):
            topics = [topics]
        signature = self.group_blockchain.member_did_manager.sign(content)
        block_content = (
            self.group_blockchain.member_did_manager.did.encode() +
            bytearray([0]) + signature
        )
        if self.virtual_layer_name:
            topics = [self.virtual_layer_name] + topics
        
        base_block = self.base_blockchain.add_block(block_content, topics)
        block = DataBlock(base_block, content, author=self.group_blockchain)
        self.store_block_content(block.long_id, content)
        self._blocks.add_block(block)

        return block

    def _on_block_received(self, block: GenericBlock) -> None:
        """Handle a block received by `self.base_blockchain`"""
        if self.virtual_layer_name not in block.topics:
            # logger.info(f"PB: Passing on block: {block.topics}")
            if self.other_blocks_handler:
                self.other_blocks_handler(block)
            return
        # logger.info(f"PB: Processing block: {block.topics}")
        # get and store private content
        private_content = self.get_block_content(block.long_id)
        if private_content:
            self._on_private_block_received(block, private_content)
        else:
            self._blocks_to_find.append(block)

    def _on_private_block_received(self, block: GenericBlock, private_content: bytes):
        author_did = self.get_block_author_did(block)

        # create PriBlock object from block and private content
        # call user's eventhandler
        private_block = DataBlock(block, private_content, author_did)
        self._blocks.add_block(private_block)

        if self.block_received_handler:
            self.block_received_handler(private_block)

    def ask_around_for_content(self, block: GenericBlock) -> bytes | None:
        """Try to get a block's referred off-chain data from other peers.

        No Exceptions, while loop until content is found, unless we want to
        keep track of processed blocks ourselves
        instead of letting walytis_beta_api do.
        """
        # ensure we don't process a block too soon
        block_age = (datetime.utcnow() - block.creation_time).total_seconds()
        if block_age < MIN_BLOCK_AGE_S:
            sleep(MIN_BLOCK_AGE_S - block_age)
            if self._terminate:
                return None

        private_content = self.get_block_content(block.long_id)
        if private_content:
            logger.debug("We already have this block's private content")
            return private_content
        logger.debug("Asking around for this block's private content")

        # join author's DidManager if not yet done
        i = block.content.index(bytearray([0]))
        author_did = block.content[:i].decode()
        author_blockchain_id = blockchain_id_from_did(author_did)
        signature = block.content[i + 1:]

        # look for MemberJoiningBlock for the author
        joins = [
            MemberJoiningBlock.load_from_block_content(block.content).get_member(
            ) for block in self.group_blockchain.get_member_joining_blocks()
        ]
        invitations = [
            join['invitation']
            for join in joins if join['did'] == author_did
        ]
        if not invitations:
            logger.error("Can't find block author's MemberJoiningBlock")
        invitation = invitations[-1]

        if author_blockchain_id not in walytis_beta_api.list_blockchain_ids():
            # try to join
            for i in range(5):  # TODO remove magic number
                try:
                    walytis_beta_api.join_blockchain(invitation)
                except walytis_beta_api.JoinFailureError:
                    pass
                except walytis_beta_api.BlockchainAlreadyExistsError:
                    pass
            if author_blockchain_id not in walytis_beta_api.list_blockchain_ids():
                logger.error("Couldn't join block author's DidManager")
                logger.error(invitation)
                return None
        logger.info("Joined block author's DidManager")

        # load author's DidManager
        author_did_manager = self.members.get(author_did)
        if not author_did_manager:
            # load author's DidManager
            author_did_manager = DidManager.from_blockchain_id(
                author_blockchain_id
            )
            self.members.update({author_did: author_did_manager})
        logger.info("Loaded block author's DidManager")

        private_content: bytes | None = None
        while not private_content:
            if self._terminate:
                logger.debug(
                    "Exiting ask_around_for_content because of termination")
                return None
            if not self.check_unlocked():
                sleep(1)
                continue
            # double check we haven't already got it
            private_content = self.get_block_content(block.long_id)
            if private_content:
                break
            peers = self.base_blockchain.get_peers()
            author_peer_id = block.creator_id.decode()
            author_peers = json.loads(invitation)["peers"]
            if author_peer_id in author_peers:
                author_peers.remove(author_peer_id)

            author_peers.append(author_peer_id)
            # move block author to top of list of IPFS peers
            for peer in author_peers:
                if peer in peers:
                    peers.remove(peer)
                if peer != ipfs.peer_id:
                    peers.insert(0, peer)
            logger.info(f"Asking peers: {len(peers)}")
            try:
                for peer in peers:
                    if self._terminate:
                        return None
                    logger.debug(f"Getting private content from {peer}")
                    conv = ipfs.start_conversation(
                        f"PrivateBlocks: ContentRequest: {block.ipfs_cid}",
                        peer,
                        self.content_request_listener._listener_name
                    )
                    conv.say(block.long_id, COMMS_TIMEOUT_S)
                    response = conv.listen(COMMS_TIMEOUT_S)
                    conv.close()
                    if not response:
                        continue
                    try:
                        decoded_response = self.group_blockchain.decrypt(
                            response)
                    except multi_crypt.crypt.LockedError:
                        logger.error(
                            f"CRYPT LOCKED for {self.group_blockchain.did}"
                        )
                        continue
                    if author_did_manager.verify_signature(signature, decoded_response):
                        private_content = decoded_response
                        self.store_block_content(
                            block.long_id, private_content)
                        logger.debug("Received and verified private content")
                        break
                    else:
                        logger.error(
                            "WARNING: private content signature verification failed")
            except Exception as error:

                logger.error(error)
                import traceback
                traceback.print_exc()
            if self._terminate:
                logger.debug(
                    "Exiting ask_around_for_content because of termination")
                return None
            sleep(1)
        self.store_block_content(block.long_id, private_content)
        return private_content

    def handle_content_request(self, conv_name: str, peer_id: str) -> None:
        if self._terminate:
            return
        conv = ipfs.join_conversation(
            conv_name + peer_id,
            peer_id,
            conv_name,
        )
        block_id = conv.listen(timeout=COMMS_TIMEOUT_S)
        content = self.get_block_content(block_id)
        if content:
            private_content = self.group_blockchain.encrypt(content)
            conv.say(private_content, timeout_sec=COMMS_TIMEOUT_S)
        conv.close()

    def get_peers(self) -> list[str]:
        return self.base_blockchain.get_peers()

    @property
    def blockchain_id(self):
        return self.base_blockchain.blockchain_id

    def terminate(self, **kwargs) -> None:
        if self._terminate:
            return
        self._terminate = True
        self.group_blockchain.terminate(**kwargs)
        self.base_blockchain.terminate(**kwargs)
        self.content_request_listener.terminate()
        blockstore.BlockStore.terminate(self)
        for did_manager in self.members.values():
            logger.info("Terminating member...")
            did_manager.terminate()
        self._blocks_to_find_thr.join()
        logger.info("PB: TERMINATED!")

    def delete(self) -> None:
        self.terminate()

        try:
            self.group_blockchain.delete()
        except walytis_beta_api.NoSuchBlockchainError:
            pass
        try:
            self.base_blockchain.delete()
        except walytis_beta_api.NoSuchBlockchainError:
            pass

    def __del__(self) -> None:
        self.terminate()

    def check_unlocked(self) -> bool:
        if not self.group_blockchain.get_control_key().private_key:
            logger.debug(
                f"PB: GroupDidManager is locked: {self.group_blockchain.did}"
            )
            return False
        else:
            logger.debug(
                f"PB: GroupDidManager is unlocked: {self.group_blockchain.did}"
            )
            return True
