import os
import tempfile

import _testing_utils
import walytis_offchain
import pytest
import walytis_identities
from walytis_offchain import PrivateBlockchain
from walytis_identities.did_manager import DidManager
from walytis_identities.did_objects import Key
from walytis_identities.group_did_manager import GroupDidManager
from walytis_identities.key_store import KeyStore
from walytis_beta_embedded._walytis_beta.walytis_beta_api._experimental import generic_blockchain_testing
from walytis_beta_embedded._walytis_beta.walytis_beta_api._experimental.generic_blockchain_testing import (
    test_generic_blockchain,
)

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


def test_preparations():
    pytest.did_config_dir = tempfile.mkdtemp()
    pytest.key_store_path = os.path.join(
        pytest.did_config_dir, "master_keystore.json")

    # the cryptographic family to use for the tests
    pytest.CRYPTO_FAMILY = "EC-secp256k1"
    pytest.KEY = Key.create(pytest.CRYPTO_FAMILY)

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



def test_cleanup():
    pytest.private_blockchain.delete()
    pytest.group_did_manager.delete()


def test_generic_blockchain_features():
    pytest.private_blockchain = test_generic_blockchain(
        PrivateBlockchain, group_blockchain=pytest.group_did_manager)


def run_tests():
    test_preparations()
    test_generic_blockchain_features()
    test_cleanup()


if __name__ == "__main__":
    generic_blockchain_testing.PYTEST = False
    generic_blockchain_testing.BREAKPOINTS=True
    run_tests()
