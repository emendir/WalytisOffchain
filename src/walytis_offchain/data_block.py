from __future__ import annotations

from typing import Type, TypeVar

from walytis_identities.group_did_manager import GroupDidManager
from walytis_beta_api import BlockNotFoundError
from walytis_beta_tools._experimental.block_lazy_loading import BlocksList
from walytis_beta_api._experimental.generic_blockchain import GenericBlock

from walytis_beta_api._experimental.generic_blockchain import GenericBlockchain


class DataBlock(GenericBlock):
    
    def __init__(
        self, block: GenericBlock,
        content: bytes | bytearray | None = None,
        author: GroupDidManager | None = None
    ):
        self.base_block = block
        self._content = content
        self._author = author
    @property
    def content(self):
        return self._content
    @property
    def author(self):
        return self._author
    @staticmethod
    def from_id(
        block_id: bytearray | bytes, blockchain: GenericBlockchain
    ) -> 'DataBlock':
        return DataBlock.from_block(block_id, blockchain)

    @staticmethod
    def from_block(
        block_id: bytearray | bytes | GenericBlock, blockchain: GenericBlockchain
    ) -> 'DataBlock':
        return blockchain.load_block(block_id)

    @property
    def ipfs_cid(self):
        return self.base_block.ipfs_cid

    @property
    def short_id(self):
        return self.base_block.short_id

    @property
    def long_id(self):
        return self.base_block.long_id

    @property
    def creator_id(self):
        return self.base_block.creator_id

    @property
    def creation_time(self):
        return self.base_block.creation_time

    @property
    def topics(self):
        return self.base_block.topics[1:]

    @property
    def parents(self):
        return self.base_block.parents

    @property
    def file_data(self):
        return self.base_block.file_data


# a type variable restricted to subclasses of Block
BlockType = TypeVar('BlockType', bound=DataBlock)


class DataBlocksList(BlocksList[BlockType]):
    def __init__(self, blockchain: GenericBlockchain, block_class: Type[BlockType] = DataBlock):
        BlocksList.__init__(self, block_class)
        self.blockchain = blockchain

    @classmethod
    def from_blocks(
        cls: Type['BlocksList[BlockType]'],
        blocks: list[BlockType],
        blockchain: GenericBlockchain,
        block_class: Type[BlockType]
    ) -> 'BlocksList[BlockType]':
        # if blocks and not isinstance(blocks[0], block_class):
        #     raise TypeError(
        #         f"Blocks are of type {type(blocks[0])}, not {block_class}"
        #     )
        # Use dict.fromkeys() to create the dictionary efficiently
        blocks_dict = dict([
            (bytes(block.long_id), block) for block in blocks
        ])

        # Cast the dictionary to an instance of BlocksList
        # Create an uninitialized instance of the class
        blocks_list = cls.__new__(cls)

        # Manually initialize the dictionary part with the data
        blocks_list.update(blocks_dict)

        # Manually set the block_class
        blocks_list.block_class = block_class
        blocks_list.blockchain = blockchain

        return blocks_list

    @classmethod
    def from_block_ids(
        cls: Type['BlocksList[BlockType]'],
        block_ids: list[bytes],
        blockchain: GenericBlockchain,
        block_class: Type[BlockType] = DataBlock
    ) -> 'BlocksList[BlockType]':

        if block_ids and bytearray([0, 0, 0, 0]) not in bytearray(block_ids[0]):
            print(block_ids[0])
            raise ValueError(
                "It looks like you passed an short ID or invalid ID as a parameter.")
        if block_ids and isinstance(block_ids[0], bytearray):
            block_ids = [bytes(block_id) for block_id in block_ids]
        # Use dict.fromkeys() to create the dictionary efficiently
        blocks_dict = dict.fromkeys(block_ids, None)

        # Cast the dictionary to an instance of BlocksList
        # Create an uninitialized instance of the class
        blocks_list = cls.__new__(cls)

        # Manually initialize the dictionary part with the data
        blocks_list.update(blocks_dict)

        # Manually set the block_class
        blocks_list.block_class = block_class
        blocks_list.blockchain = blockchain

        return blocks_list

    def __getitem__(self,  block_id: bytes) -> BlockType:
        try:
            block: BlockType = dict.__getitem__(self, block_id)
        except KeyError:
            if bytearray([0, 0, 0, 0]) not in block_id:
                raise ValueError(
                    "It looks like you passed an short ID or invalid ID as a parameter.")
            else:
                raise BlockNotFoundError("PB: Couldn't find this block_id in BlocksList")
        if not block or not isinstance(block, self.block_class):
            block = self.block_class.from_id(block_id, self.blockchain)
            dict.__setitem__(self, block_id, block)
        return block
