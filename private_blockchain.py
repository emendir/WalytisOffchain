import blockstore
import data_block
from data_block import DataBlock
from ipfs_datatransmission import ConversationListener, join_conversation, start_conversation
from identity.identity import IdentityAccess
from typing import Callable
from generic_blockchain import Blockchain, Block
COMMS_TIMEOUT_S = 30


class PrivateBlockchain(blockstore.BlockStore):
    def __init__(
        self,
        identity: IdentityAccess,
        base_blockchain_type,
        blockchain_id: str,
        block_received_handler: Callable[[Block], None] | None = None,
        app_name: str = "",
        appdata_dir: str = "",
        auto_load_missed_blocks: bool = True,
        forget_appdata: bool = False,
        sequential_block_handling: bool = True,
        update_blockids_before_handling: bool = False,
    ):
        self.identity = identity
        self.base_blockchain: Blockchain = base_blockchain_type(
            blockchain_id=blockchain_id,
            app_name=app_name,
            block_received_handler=self._on_block_received,
            auto_load_missed_blocks=auto_load_missed_blocks,
            forget_appdata=forget_appdata,
            sequential_block_handling=sequential_block_handling
        )
        self.block_received_handler = block_received_handler

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

    def get_block_ids(self) -> list[bytes | bytearray]:
        return self.base_blockchain.block_ids

    def get_blocks(self) -> list[DataBlock]:
        return [
            self.load_block(block_id)
            for block_id in self.base_blockchain.block_ids
        ]

    def add_block(
        self, content: bytes, topics: str | list[str] = []
    ) -> DataBlock:
        block_content = self.identity.sign(content)
        block = self.base_blockchain.add_block(block_content, topics)
        self.store_block_content(block.short_id, content)
        return DataBlock(block, content)

    def _on_block_received(self, block: Block) -> None:
        # get and store private content
        author, private_content = self.ask_around_for_content(
            block)  # block content is content_id
        self.store_block_content(block.short_id, private_content)
        self.store_block_author(block.short_id, author)
        # create PriBlock object from block and private content
        # call user's eventhandler
        private_block = DataBlock(block, private_content, author)
        self.block_received_handler(private_block)

    def ask_around_for_content(self, block: Block):
        """
        No Exceptions, while loop until content is found, unless we want to
        keep track of processed blocks ourselves
        instead of letting walytis_beta_api do.
        """
        peers = self.base_blockchain.get_peers()
        # move block author to top of list
        peers.remove(block.creator_id)
        peers.insert(0, block.creator_id)

        private_content: bytes | None = None
        while not private_content:
            try:
                for peer in peers:
                    conv = start_conversation(
                        f"PrivateBlocks:ContentRequest:{block.ipfs_cid}",
                        peer,
                        self.content_request_listener._listener_name
                    )
                    response = conv.say(block.short_id, COMMS_TIMEOUT_S)
                    conv.close()

                    author = self.identity.verify(response, block.content)
                    if author:
                        private_content = response
                        break
                    else:
                        print(
                            "WARNING: private content signature verification failed")
            except Exception as error:
                print(error)
            # refresh list of peers
            peers = self.base_blockchain.get_peers()
        return DataBlock(block, self.identity.decrypt(private_content), author)

    def handle_content_request(self, conv_name: str, peer_id: str) -> None:
        conv = join_conversation(
            conv_name+peer_id,
            peer_id,
            conv_name,
        )
        block_id = conv.listen(timeout=COMMS_TIMEOUT_S)
        private_content = self.identity.encrypt(self.get_block_content(block_id))
        conv.say(private_content, timeout_sec=COMMS_TIMEOUT_S)
        conv.close()

    def terminate(self) -> None:
        self.base_blockchain.terminate()

    def __del__(self) -> None:
        self.terminate()
