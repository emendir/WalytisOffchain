import os
import shutil
import tempfile
import threading

import _testing_utils
import walytis_offchain
import pytest
import walytis_identities
import walytis_beta_api as waly
from _testing_utils import mark, test_threads_cleanup
from walytis_offchain import PrivateBlockchain
from walytis_identities.did_manager import DidManager
from walytis_identities.did_objects import Key
from walytis_identities.group_did_manager import GroupDidManager
from walytis_identities.key_store import KeyStore

_testing_utils.assert_is_loaded_from_source(
    source_dir=os.path.dirname(os.path.dirname(__file__)),
    module=walytis_offchain
)
_testing_utils.assert_is_loaded_from_source(
    source_dir=os.path.join(
        os.path.abspath(__file__), "..", "..", "..", "walytis_identities", "src"
    ),
    module=walytis_identities
)


waly.log.PRINT_DEBUG = False


REBUILD_DOCKER = True

# automatically remove all docker containers after failed tests
DELETE_ALL_BRENTHY_DOCKERS = True
if _testing_utils.WE_ARE_IN_DOCKER:
    REBUILD_DOCKER = False
    DELETE_ALL_BRENTHY_DOCKERS = False


def test_preparations() -> None:
    """Setup resources in preparation for tests."""
    # declare 'global' variables
    pytest.did_config_dir = tempfile.mkdtemp()
    pytest.key_store_path = os.path.join(
        pytest.did_config_dir, "master_keystore.json")

    # the cryptographic family to use for the tests
    pytest.CRYPTO_FAMILY = "EC-secp256k1"
    pytest.KEY = Key.create(pytest.CRYPTO_FAMILY)

    pytest.group_did_manager = None
    pytest.pri_blockchain = None


threading.enumerate()


def test_terminate():
    pytest.pri_blockchain.terminate()


def cleanup():
    if pytest.pri_blockchain:
        pytest.pri_blockchain.delete()
    shutil.rmtree(pytest.did_config_dir)


HELLO_THERE = "Hello there!".encode()


def create_private_blockchain() -> None:
    device_keystore_path = os.path.join(
        pytest.did_config_dir, "device_keystore.json")
    profile_keystore_path = os.path.join(
        pytest.did_config_dir, "profile_keystore.json")

    device_did_keystore = KeyStore(device_keystore_path, pytest.KEY)
    profile_did_keystore = KeyStore(profile_keystore_path, pytest.KEY)
    pytest.member_1 = DidManager.create(device_did_keystore)
    pytest.group_did_manager = GroupDidManager.create(
        profile_did_keystore, pytest.member_1
    )

    pytest.pri_blockchain = PrivateBlockchain(pytest.group_did_manager)
    mark(
        isinstance(pytest.pri_blockchain, PrivateBlockchain),
        "Create GroupDidManager"
    )


def test_add_block():
    """Test that we can create a PrivateBlockchain and add a block."""
    print("Creating private blockchain...")
    block = pytest.pri_blockchain.add_block(HELLO_THERE)
    blockchain_blocks = list(pytest.pri_blockchain.get_blocks())
    mark(
        blockchain_blocks and
        blockchain_blocks[-1].content == block.content == HELLO_THERE,
        "Created private blockchain, added block"
    )


def run_tests():
    print("\nRunning tests for Private Blockchain:")
    test_preparations()
    create_private_blockchain()
    test_add_block()
    test_terminate()
    test_threads_cleanup()
    cleanup()


if __name__ == "__main__":
    _testing_utils.PYTEST = False
    _testing_utils.BREAKPOINTS = True
    run_tests()
