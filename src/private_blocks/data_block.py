from walidentity.group_did_manager import GroupDidManager
from walytis_beta_api.generic_blockchain import GenericBlock


class DataBlock(GenericBlock):
    content: bytes | bytearray = bytearray()

    def __init__(self, block: GenericBlock, content: bytes | bytearray, author: GroupDidManager):
        self.base_block = block
        self.content = content
        self.author = author

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
