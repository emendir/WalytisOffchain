import walytis_api


class DataBlock():
    def __init__(self, block, private_content, author):
        self.base_block = block
        self.secure_content = private_content
        self.author = author

    def get_id(self):
        return self.base_block.short_id
