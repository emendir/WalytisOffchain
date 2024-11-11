import os

import _testing_utils
import private_blocks
import pytest
import walidentity
from prebuilt_group_did_managers import (
    load_did_manager,
)
from private_blocks import PrivateBlockchain
from walytis_beta_api._experimental.generic_blockchain_testing import (
    test_generic_blockchain,
)

_testing_utils.assert_is_loaded_from_source(
    source_dir=os.path.dirname(os.path.dirname(__file__)),
    module=private_blocks
)
_testing_utils.assert_is_loaded_from_source(
    source_dir=os.path.join(
        os.path.abspath(__file__), "..", "..", "..", "WalIdentity", "src"
    ),
    module=walidentity
)


def test_preparations():

    tarfile = "group_did_manager_2.tar"
    pytest.group_did_manager = load_did_manager(os.path.join(
        os.path.dirname(__file__),
        tarfile
    ))


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
    run_tests()
