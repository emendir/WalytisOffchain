import rocksdb
import shutil
import appdirs
import os


class BlockStore:
    content_db_path: str

    def init_blockstore(self):
        self.appdata_path = os.path.join(
            appdirs.user_data_dir(),
            "PrivateBlocks",
            self.base_blockchain.blockchain_id
        )
        if not os.path.exists(self.appdata_path):
            os.makedirs(self.appdata_path)

        self.content_db_path = os.path.join(self.appdata_path, "BlockContent")
        self.authors_db_path = os.path.join(self.appdata_path, "BlockAuthors")

        self.content_db = rocksdb.DB(
            self.content_db_path, rocksdb.Options(create_if_missing=True))
        self.authors_db = rocksdb.DB(
            self.authors_db_path, rocksdb.Options(create_if_missing=True))

    def store_block_content(self, block_id: bytes, content: bytes):
        self.content_db.put(block_id, content)

    def get_block_content(self, block_id: bytes):
        return self.content_db.get(block_id)

    def get_block_author(self, block_id: bytes):
        return self.authors_db.get(block_id)

    def store_block_author(self, block_id: bytes, author: bytes):
        self.authors_db.put(block_id, author)

    def terminate(self):
        self.content_db.close()
        self.authors_db.close()

    def __del__(self):
        self.terminate()
