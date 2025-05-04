import sqlite3
import shutil
import appdirs
import os
from walytis_offchain.threaded_object import DedicatedThreadClass, run_on_dedicated_thread


_PRIVATE_BLOCKS_DATA_DIR = os.getenv("PRIVATE_BLOCKS_DATA_DIR", "")
if _PRIVATE_BLOCKS_DATA_DIR:
    PRIVATE_BLOCKS_DATA_DIR = _PRIVATE_BLOCKS_DATA_DIR
else:
    PRIVATE_BLOCKS_DATA_DIR = "."


class BlockStore(DedicatedThreadClass):
    content_db_path: str
    def __init__(self):
        DedicatedThreadClass.__init__(self)
    @run_on_dedicated_thread
    def init_blockstore(self):
        self.appdata_path = os.path.join(
            PRIVATE_BLOCKS_DATA_DIR,
            self.base_blockchain.blockchain_id
        )
        if not os.path.exists(self.appdata_path):
            os.makedirs(self.appdata_path)

        self.content_db_path = os.path.join(
            self.appdata_path, "BlockContent.db")


        self.content_db = sqlite3.connect(self.content_db_path)

        self._create_tables()

    @run_on_dedicated_thread
    def _create_tables(self):
        with self.content_db:
            self.content_db.execute('''
                CREATE TABLE IF NOT EXISTS BlockContent (
                    block_id BLOB PRIMARY KEY,
                    content BLOB
                )
            ''')



    @run_on_dedicated_thread
    def get_known_blocks(self) -> list[bytes]:
        """Get a the block IDs of the blocks whose private content we have."""
        cursor = self.content_db.cursor()
        cursor.execute('SELECT block_id FROM BlockContent;')
        results = cursor.fetchall()
        return [r[0] for r in results] if results else []
    @run_on_dedicated_thread
    def store_block_content(self, block_id: bytes | bytearray, content: bytes | bytearray):
        with self.content_db:
            self.content_db.execute('''
                INSERT OR REPLACE INTO BlockContent (block_id, content)
                VALUES (?, ?)
            ''', (block_id, content))

    @run_on_dedicated_thread
    def get_block_content(self, block_id: bytes):
        cursor = self.content_db.cursor()
        cursor.execute('''
            SELECT content FROM BlockContent WHERE block_id = ?
        ''', (block_id,))
        result = cursor.fetchone()
        return result[0] if result else None



    @run_on_dedicated_thread
    def terminate(self):
        self.content_db.close()
        DedicatedThreadClass.terminate(self)

    def __del__(self):
        self.terminate()
