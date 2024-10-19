from typing import Callable

import walytis_beta_api
from ipfs_datatransmission import (
    ConversationListener,
    join_conversation,
    start_conversation,
)
from walidentity.did_manager import DidManager
from walidentity.group_did_manager import GroupDidManager
from walytis_beta_api import decode_short_id
from walytis_beta_api.generic_blockchain import GenericBlock, GenericBlockchain

from . import blockstore
from .data_block import DataBlock
# from loguru import logger
COMMS_TIMEOUT_S = 30


class PrivateBlockchain(blockstore.BlockStore, GenericBlockchain):
    block_received_handler: Callable[[GenericBlock], None] | None = None

    def __init__(
        self,
        blockchain_identity: GroupDidManager,
        member_identity: DidManager | None = None,
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
            blockchain_identity: the object for managing this blockchain's
                participants, used for encryption in transmission of blocks'
                off-chain content
            member_identity: the object for authenticating blocks we create.
                If `None`, `blockchain_identity.member_did_manager` is used.
            base_blockchain: the blockchain to be used for storing the
                PrivateBlocks (actual content is off-chain).
                If `None`, `blockchain_identity.blockchain`
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
        # logger.info(f"PB: Initialising Private Blockchain: {virtual_layer_name}")

        self.blockchain_identity = blockchain_identity
        if base_blockchain:
            self.base_blockchain = base_blockchain
        else:
            self.base_blockchain = (
                self.blockchain_identity.blockchain
            )
        if not member_identity:
            member_identity = self.blockchain_identity.member_did_manager
        self.member_identity = member_identity
        self.block_received_handler = block_received_handler
        self.virtual_layer_name = virtual_layer_name
        self.other_blocks_handler = other_blocks_handler
        if not virtual_layer_name:
            raise ValueError(
                "`virtual_layer_name` cannot be empty!"
            )
        self.init_blockstore()
        self.content_request_listener = ConversationListener(
            listener_name=f"PrivateBlocks{self.base_blockchain.blockchain_id}",
            eventhandler=self.handle_content_request
        )

    def load_block(self, block_id: bytes) -> DataBlock:
        content = self.get_block_content(block_id)
        author = self.get_block_author(block_id)
        block = self.base_blockchain.get_block(block_id)
        return DataBlock(block, content, author)

    def get_blocks(self) -> list[DataBlock]:
        return [
            self.load_block(block_id)
            for block_id in self.block_ids
        ]

    def add_block(
        self, content: bytes, topics: str | list[str] = []
    ) -> DataBlock:
        if isinstance(topics, str):
            topics = [topics]
        signature = self.member_identity.sign(content)
        block_content = self.member_identity.did.encode()+bytearray([0])+signature
        if self.virtual_layer_name:
            topics = [self.virtual_layer_name]+topics
        block = self.base_blockchain.add_block(block_content, topics)
        self.store_block_content(block.short_id, content)
        return DataBlock(block, content, author=self.member_identity)

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
        self.store_block_content(block.short_id, private_content)
        self.store_block_author(block.short_id, author)
        # create PriBlock object from block and private content
        # call user's eventhandler
        private_block = DataBlock(block, private_content, author)
        if self.block_received_handler:
            self.block_received_handler(private_block)

    def ask_around_for_content(self, block: GenericBlock) -> DataBlock:
        """Try to get a block's referred off-chain data from other peers.

        No Exceptions, while loop until content is found, unless we want to
        keep track of processed blocks ourselves
        instead of letting walytis_beta_api do.
        """
        signature = block.content[:i]
        author_blockchain_id = block.content[i+1:]
        if author_blockchain_id not in walytis_beta_api.list_blockchain_ids():
            walytis_beta_api.join_blockchain(author_blockchain_id)
        author = DidManager(author_blockchain_id)
        peers = self.base_blockchain.get_peers()
        # move block author to top of list
        peers.remove(block.creator_id)
        peers.insert(0, block.creator_id)

        private_content: bytes | None = None
        while not private_content:
            try:
                for peer in peers:
                    conv = start_conversation(
                        f"PrivateBlocks: ContentRequest: {block.ipfs_cid}",
                        peer,
                        self.content_request_listener._listener_name
                    )
                    response = conv.say(block.short_id, COMMS_TIMEOUT_S)
                    conv.close()
                    decoded_response = self.blockchain_identity.decrypt(response)
                    if author.verify(decoded_response, signature):
                        private_content = decoded_response
                        break
                    else:
                        print(
                            "WARNING: private content signature verification failed")
            except Exception as error:
                print(error)
            # refresh list of peers
            peers = self.base_blockchain.get_peers()
        i = block.content.index(bytearray([0]))

        return DataBlock(block, private_content, author)

    def handle_content_request(self, conv_name: str, peer_id: str) -> None:
        conv = join_conversation(
            conv_name + peer_id,
            peer_id,
            conv_name,
        )
        block_id = conv.listen(timeout=COMMS_TIMEOUT_S)
        content = self.get_block_content(block_id)
        if content:
            private_content = self.blockchain_identity.encrypt(content)
            conv.say(private_content, timeout_sec=COMMS_TIMEOUT_S)
        conv.close()

    def get_peers(self) -> list[str]:
        return self.base_blockchain.get_peers()

    @property
    def block_ids(self):
        return [
            block_id for block_id in self.base_blockchain.block_ids
            if self.virtual_layer_name in decode_short_id(block_id)["topics"]
        ]

    @property
    def blockchain_id(self):
        return self.base_blockchain.blockchain_id

    def get_block(self, block_id: bytes | bytearray | int):
        if isinstance(block_id, int):
            block_id = self.block_ids[block_id]
        return self.load_block(block_id)

    def terminate(self) -> None:
        self.blockchain_identity.terminate()
        self.base_blockchain.terminate()
        self.content_request_listener.terminate()

    def delete(self) -> None:
        self.terminate()
        try:
            self.blockchain_identity.delete()
        except walytis_beta_api.NoSuchBlockchainError:
            pass
        try:
            self.base_blockchain.delete()
        except walytis_beta_api.NoSuchBlockchainError:
            pass

    def __del__(self) -> None:
        self.terminate()
