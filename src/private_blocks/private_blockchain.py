import threading
from time import sleep
import json
import ipfs_api
from walidentity.did_manager_with_supers import DidManagerWithSupers
from walidentity.did_manager_blocks import MemberJoiningBlock
from typing import Callable
from loguru import logger
import walytis_beta_api
from ipfs_datatransmission import (
    ConversationListener,
    join_conversation,
    start_conversation,
)
from walidentity.did_manager import DidManager
from walidentity.group_did_manager import GroupDidManager
from walytis_beta_api import decode_short_id
from walytis_beta_api._experimental.generic_blockchain import GenericBlock, GenericBlockchain
from walidentity.did_manager import blockchain_id_from_did
from . import blockstore
from .data_block import DataBlock, DataBlocksList
# from loguru import logger
COMMS_TIMEOUT_S = 30


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
        self._terminate=False
        blockstore.BlockStore.__init__(self)
        self.group_blockchain = group_blockchain
        group_blockchain.block_received_handler = self._on_block_received

        if base_blockchain:
            self.base_blockchain = base_blockchain
        else:
            self.base_blockchain = self.group_blockchain

        self.virtual_layer_name = virtual_layer_name
        # logger.info(f"PB: Initialising Private Blockchain: {virtual_layer_name}")
        
        self.init_blockstore()
        known_blocks = self.get_known_blocks()
        blocks = [
            block for block in self.base_blockchain.get_blocks()

            if self.virtual_layer_name in block.topics
            and block.long_id in known_blocks
        ]
        self._blocks = DataBlocksList.from_blocks(blocks, self, DataBlock)

        self.block_received_handler = block_received_handler
        self.other_blocks_handler = other_blocks_handler
        if not virtual_layer_name:
            raise ValueError(
                "`virtual_layer_name` cannot be empty!"
            )
        self.content_request_listener = ConversationListener(
            listener_name=f"PrivateBlocks{self.base_blockchain.blockchain_id}",
            eventhandler=self.handle_content_request
        )

        self.base_blockchain.block_received_handler = self._on_block_received
        # list to store members' DidManagers in
        self.members = {
            self.group_blockchain.member_did_manager.did: self.group_blockchain.member_did_manager
        }
    def load_block(self, block: bytes | GenericBlock) -> DataBlock:
        if isinstance(block, bytes | bytearray):
            block = self.base_blockchain.get_block(block)
        content = self.get_block_content(block.long_id)
        author = self.get_block_author(block.long_id)
        return DataBlock(block, content, author)

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
        block_content = self.group_blockchain.member_did_manager.did.encode() + \
            bytearray([0]) + signature
        if self.virtual_layer_name:
            topics = [self.virtual_layer_name] + topics
        base_block = self.base_blockchain.add_block(block_content, topics)
        block = DataBlock(base_block, content, author=self.group_blockchain)
        self.store_block_content(block.long_id, content)
        self.store_block_author(
            block.long_id, self.group_blockchain.member_did_manager.did)
        self._blocks.add_block(block)

        return block


    def _on_block_received(self, block: GenericBlock) -> None:
        if self.virtual_layer_name not in block.topics:
            # logger.info(f"PB: Passing on block: {block.topics}")
            if self.other_blocks_handler:
                self.other_blocks_handler(block)
            return
        # logger.info(f"PB: Processing block: {block.topics}")
        # get and store private content
        author, private_content = self.ask_around_for_content(
            block)  # block content is content_id
        
        # create PriBlock object from block and private content
        # call user's eventhandler
        private_block = DataBlock(block, private_content, author)
        self._blocks.add_block(private_block)
        
        if self.block_received_handler:
            self.block_received_handler(private_block)
        

    def ask_around_for_content(self, block: GenericBlock) -> tuple[str, bytes | None]:
        """Try to get a block's referred off-chain data from other peers.

        No Exceptions, while loop until content is found, unless we want to
        keep track of processed blocks ourselves
        instead of letting walytis_beta_api do.
        """
        i = block.content.index(bytearray([0]))
        author_did = block.content[:i].decode()
        private_content = self.get_block_content(block.long_id)
        if private_content:
            return (author_did, private_content)
        signature = block.content[i + 1:]
        joins = [MemberJoiningBlock.load_from_block_content(block.content).get_member(
        ) for block in self.group_blockchain.get_member_joining_blocks()]
        invitation = [join['invitation']
                      for join in joins if join['did'] == author_did][0]
        author_blockchain_id = blockchain_id_from_did(author_did)
        if author_blockchain_id not in walytis_beta_api.list_blockchain_ids():
            for i in range(5):
                try:
                    walytis_beta_api.join_blockchain(invitation)
                except walytis_beta_api.JoinFailureError:
                    pass
        author_did_manager = self.members.get(author_did)
        
        if not author_did:
            if author_blockchain_id not in walytis_beta_api.list_blockchain_ids():
                logger.warning("Failed to join block author's blockchain")
                logger.warning(invitation)
                logger.warning(author_blockchain_id)
                return (author_did, None)
            author_did_manager = DidManager.from_blockchain_id(
                author_blockchain_id
            )
            self.members.update({author_did: author_did_manager})
        

            
        private_content: bytes | None = None
        while not private_content:
            if self._terminate:
                return (author_did, None)
            private_content = self.get_block_content(block.long_id)
            if private_content:
                break
            if self._terminate:
                return (author_did, None)
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
                if peer != ipfs_api.my_id():
                    peers.insert(0, peer)
                    
                
            try:
                for peer in peers:
                    if self._terminate:
                        return (author_did, None)
                            
                    conv = start_conversation(
                        f"PrivateBlocks: ContentRequest: {block.ipfs_cid}",
                        peer,
                        self.content_request_listener._listener_name
                    )
                    conv.say(block.long_id, COMMS_TIMEOUT_S)
                    response = conv.listen(COMMS_TIMEOUT_S)
                    conv.close()
                    if not response:
                        continue
                    decoded_response = self.group_blockchain.decrypt(response)
                    if author_did_manager.verify(decoded_response, signature):
                        private_content = decoded_response
                        self.store_block_content(block.long_id, private_content)
                        self.store_block_author(block.long_id, author_did)

                        break
                    else:
                        logger.error(
                            "WARNING: private content signature verification failed")
            except Exception as error:

                logger.error(error)
                import traceback
                traceback.print_exc()
            if self._terminate:
                return (author_did, None)
            sleep(1)

        return (author_did, private_content)

    def handle_content_request(self, conv_name: str, peer_id: str) -> None:
        conv = join_conversation(
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
