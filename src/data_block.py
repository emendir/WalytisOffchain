import walytis_beta_api
from walytis_beta_api.generic_blockchain import GenericBlock


class DataBlock(GenericBlock):
    def __init__(self, block, private_content, author=None):
        self.base_block = block
        self.private_content = private_content
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
        return self.base_block.topics

    @property
    def content(self):
        return self.base_block.content

    @property
    def parents(self):
        return self.base_block.parents

    @property
    def file_data(self):
        return self.base_block.file_data
