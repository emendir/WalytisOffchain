import os
import tempfile

import walytis_offchain
import pytest
import walytis_identities
from walytis_offchain import PrivateBlockchain
from walytis_identities.did_manager import DidManager
from walytis_identities.key_objects import Key
from walytis_identities.group_did_manager import GroupDidManager
from walytis_identities.key_store import KeyStore
from walytis_beta_api._experimental import generic_blockchain_testing
from walytis_beta_api._experimental.generic_blockchain_testing import (
    run_generic_blockchain_test,
)



class SharedData():
    pass
shared_data = SharedData()
def test_preparations():
    shared_data.did_config_dir = tempfile.mkdtemp()
    shared_data.key_store_path = os.path.join(
        shared_data.did_config_dir, "master_keystore.json")

    # the cryptographic family to use for the tests
    shared_data.CRYPTO_FAMILY = "EC-secp256k1"
    shared_data.KEY = Key.create(shared_data.CRYPTO_FAMILY)

    device_keystore_path = os.path.join(
        shared_data.did_config_dir, "device_keystore.json")
    profile_keystore_path = os.path.join(
        shared_data.did_config_dir, "profile_keystore.json")

    device_did_keystore = KeyStore(device_keystore_path, shared_data.KEY)
    profile_did_keystore = KeyStore(profile_keystore_path, shared_data.KEY)
    shared_data.member_1 = DidManager.create(device_did_keystore)
    shared_data.group_did_manager = GroupDidManager.create(
        profile_did_keystore, shared_data.member_1
    )




def test_generic_blockchain_features():
    shared_data.private_blockchain = run_generic_blockchain_test(
        PrivateBlockchain, group_blockchain=shared_data.group_did_manager)


def cleanup():
    if shared_data.private_blockchain:
        shared_data.private_blockchain.delete()
    if shared_data.group_did_manager:
        shared_data.group_did_manager.delete()

from emtest import await_thread_cleanup
def test_threads_cleanup() -> None:
    """Test that no threads are left running."""
    cleanup()
    assert await_thread_cleanup(timeout=5)
