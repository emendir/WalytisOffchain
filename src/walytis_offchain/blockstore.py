import sqlite3
from abc import ABC, abstractproperty
import os
from walytis_identities.group_did_manager import GroupDidManager
from walytis_identities.key_objects import Key, KeyGroup
from walytis_identities.key_store import KeyStore
from walytis_offchain.threaded_object import (
    DedicatedThreadClass,
    run_on_dedicated_thread,
)
from .log import logger_blockstore as logger
from walytis_identities.did_manager import CTRL_KEY_FAMILIES


_PRIVATE_BLOCKS_DATA_DIR = os.getenv("PRIVATE_BLOCKS_DATA_DIR", "")
if _PRIVATE_BLOCKS_DATA_DIR:
    PRIVATE_BLOCKS_DATA_DIR = _PRIVATE_BLOCKS_DATA_DIR
else:
    PRIVATE_BLOCKS_DATA_DIR = "."

# maximum number of times to use any key for encrypting private content in the database
MAX_KEY_USAGE = 20


class BlockStore(ABC, DedicatedThreadClass):
    content_db_path: str

    @abstractproperty
    def group_blockchain() -> GroupDidManager:
        pass

    def __init__(self):
        DedicatedThreadClass.__init__(self)
        self.key_usage: dict[str, int] = {}
        self._current_key = None

    def get_current_blockstore_key(self) -> KeyGroup:
        if not self._current_key:
            new_key = self.keystore.add_keygroup(
                KeyGroup([Key.create(family) for family in CTRL_KEY_FAMILIES])
            )
            self.key_usage.update({new_key.get_id(): 0})
            self._current_key = new_key

        return self._current_key

    @run_on_dedicated_thread
    def init_blockstore(
        self,
    ):
        self.appdata_path = os.path.join(
            PRIVATE_BLOCKS_DATA_DIR, self.base_blockchain.blockchain_id
        )
        if not os.path.exists(self.appdata_path):
            os.makedirs(self.appdata_path)

        self.content_db_path = os.path.join(
            self.appdata_path, "BlockContent.db"
        )
        self.keystore_path = os.path.join(
            self.appdata_path, "BlockContentDbKeys.json"
        )
        # if block-content-db-keystore already exists,
        # unlock it from key stored in the GDM's keystore
        if os.path.exists(self.keystore_path):
            key_param = self.group_blockchain.key_store
            assert key_param is not None, "BLOCKSTORE USE KEYSTORE NONE"
        else:
            # if block-content-db-keystore doesn't already exist,
            # create a key for it, storing it in the GDM's keystore
            key_param = self.group_blockchain.key_store.add_keygroup(
                KeyGroup([Key.create(family) for family in CTRL_KEY_FAMILIES])
            )
            assert key_param is not None, "BLOCKSTORE CREATE KEY NONE"
        self.keystore = KeyStore(self.keystore_path, key_param)

        self.content_db = sqlite3.connect(self.content_db_path)

        self._create_tables()

        self._load_blockstore_keys()

    @run_on_dedicated_thread
    def _create_tables(self):
        with self.content_db:
            self.content_db.execute("""
                CREATE TABLE IF NOT EXISTS BlockContent (
                    block_id BLOB PRIMARY KEY,
                    content BLOB,
                    key_id TEXT
                )
            """)

    def _load_blockstore_keys(self) -> None:
        cursor = self.content_db.cursor()
        cursor.execute("""

        SELECT
            key_id,
            COUNT(*) AS value_count
        FROM BlockContent
        GROUP BY key_id;
        """)

        results = cursor.fetchall()
        self.key_usage = dict(results)

    @run_on_dedicated_thread
    def get_known_blocks(self) -> list[bytes]:
        """Get a the block IDs of the blocks whose private content we have."""
        cursor = self.content_db.cursor()
        cursor.execute("SELECT block_id FROM BlockContent;")
        results = cursor.fetchall()
        return [r[0] for r in results] if results else []

    @run_on_dedicated_thread
    def store_block_content(
        self, block_id: bytes | bytearray, content: bytes | bytearray
    ):
        key = self.get_current_blockstore_key()
        encrypted_content = key.encrypt(content)

        with self.content_db:
            self.content_db.execute(
                """
                INSERT OR REPLACE INTO BlockContent (block_id, content, key_id)
                VALUES (?, ?, ?)
            """,
                (block_id, encrypted_content, key.get_id()),
            )
        self.key_usage[key.get_id()] += 1
        if self.key_usage[key.get_id()] >= MAX_KEY_USAGE:
            self.key_usage.pop(key.get_id())
            self._current_key = None

    @run_on_dedicated_thread
    def get_block_content(self, block_id: bytes):
        cursor = self.content_db.cursor()
        cursor.execute(
            """
            SELECT content, key_id FROM BlockContent WHERE block_id = ?
        """,
            (block_id,),
        )
        result = cursor.fetchall()
        match len(result):
            case 0:
                return None
            case 1:
                encrypted_content, key_id = result[0]
                key = self.keystore.get_keygroup(key_id)
                return key.decrypt(encrypted_content)
            case _:
                raise Exception(
                    "Found multiple entries for block in "
                    "PrivateBlocks BlockStore."
                )

    @run_on_dedicated_thread
    def terminate(self):
        self.content_db.close()
        DedicatedThreadClass.terminate(self)
        self.keystore.terminate()

    def __del__(self):
        self.terminate()
