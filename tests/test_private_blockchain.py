from emtest import await_thread_cleanup
import pytest
import _auto_run_with_pytest
import os
import shutil
import tempfile
import threading

import walytis_offchain
import walytis_identities
import walytis_beta_api as waly
from walytis_offchain import PrivateBlockchain
from walytis_offchain import blockstore
from walytis_identities.did_manager import DidManager
from walytis_identities.key_objects import Key
from walytis_identities.group_did_manager import GroupDidManager
from walytis_identities.key_store import KeyStore


REBUILD_DOCKER = True
blockstore.MAX_KEY_USAGE = 5
NUM_BLOCKS = 2 * blockstore.MAX_KEY_USAGE


class SharedData:
    def __init__(self):
        """Setup resources in preparation for tests."""
        # declare 'global' variables
        self.did_config_dir = tempfile.mkdtemp()
        self.key_store_path = os.path.join(
            self.did_config_dir, "master_keystore.json"
        )

        # the cryptographic family to use for the tests
        self.CRYPTO_FAMILY = "EC-secp256k1"
        self.KEY = Key.create(self.CRYPTO_FAMILY)

        self.group_did_manager = None
        self.pri_blockchain = None


shared_data = SharedData()


def cleanup():
    if shared_data.pri_blockchain:
        shared_data.pri_blockchain.delete()
    shutil.rmtree(shared_data.did_config_dir)


HELLO_THERE = "Hello there!".encode()


def test_create_private_blockchain() -> None:
    device_keystore_path = os.path.join(
        shared_data.did_config_dir, "device_keystore.json"
    )
    profile_keystore_path = os.path.join(
        shared_data.did_config_dir, "profile_keystore.json"
    )

    device_did_keystore = KeyStore(device_keystore_path, shared_data.KEY)
    profile_did_keystore = KeyStore(profile_keystore_path, shared_data.KEY)
    shared_data.member_1 = DidManager.create(device_did_keystore)
    shared_data.group_did_manager = GroupDidManager.create(
        profile_did_keystore, shared_data.member_1
    )

    shared_data.pri_blockchain = PrivateBlockchain(
        shared_data.group_did_manager
    )
    assert isinstance(shared_data.pri_blockchain, PrivateBlockchain), (
        "Create GroupDidManager"
    )


def _get_block_content(execution_number: int) -> bytes:
    return HELLO_THERE + f"_{execution_number}".encode()


@pytest.mark.parametrize("execution_number", range(NUM_BLOCKS))
def test_add_block(execution_number):
    """Test that we can create a PrivateBlockchain and add a block."""
    print("Creating block...")
    BLOCK_CONTENT = _get_block_content(execution_number)
    block = shared_data.pri_blockchain.add_block(BLOCK_CONTENT)
    blockchain_blocks = list(shared_data.pri_blockchain.get_blocks())
    assert blockchain_blocks
    assert blockchain_blocks[-1].content == block.content == BLOCK_CONTENT
    assert blockchain_blocks[0].content == HELLO_THERE + "_0".encode()
    assert (
        len(shared_data.pri_blockchain.keystore.get_all_keys())
        / len(blockstore.CTRL_KEY_FAMILIES)
        == (max(0, execution_number) + (blockstore.MAX_KEY_USAGE))
        // blockstore.MAX_KEY_USAGE
    ), "number of keys"


def test_reload_blockchain():
    shared_data.pri_blockchain.terminate()
    shared_data.pri_blockchain = PrivateBlockchain(
        shared_data.group_did_manager
    )
    blockchain_blocks = list(shared_data.pri_blockchain.get_blocks())
    for i in range(NUM_BLOCKS):
        BLOCK_CONTENT = _get_block_content(i)
        assert blockchain_blocks[i].content == BLOCK_CONTENT


def test_threads_cleanup() -> None:
    """Test that no threads are left running."""
    cleanup()
    assert await_thread_cleanup(timeout=5)
