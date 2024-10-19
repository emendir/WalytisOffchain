import pytest
import json
import os
import tempfile

import _testing_utils
import private_blocks
import walidentity
import walytis_beta_api as waly
from priblocks_docker.create_test_identity import (
    extract_tar_to_directory,
    key,
)
from private_blocks import PrivateBlockchain
from private_blocks.private_blockchain import PrivateBlockchain
from walidentity.group_did_manager import GroupDidManager
from walytis_beta_api.generic_blockchain_testing import test_generic_blockchain

_testing_utils.assert_is_loaded_from_source(
    source_dir=os.path.dirname(os.path.dirname(__file__)), module=private_blocks
)
_testing_utils.assert_is_loaded_from_source(
    source_dir=os.path.join(os.path.abspath(__file__), "..", "..", "..", "WalIdentity", "src"), module=walidentity
)


def test_preparations():

    # choose which group_did_manager to load
    if os.path.exists("/opt/we_are_in_docker"):
        appdata_path = "/opt/PB_TestIdentity"
    else:
        appdata_path = tempfile.mkdtemp()
        extract_tar_to_directory(
            os.path.join(
                os.path.dirname(__file__),
                "priblocks_docker",
                "group_did_manager_2.tar"
            ),
            appdata_path
        )

    # join the group_did_manager' blockchains
    with open(os.path.join(appdata_path, "group_did_metadata.json"), "r") as file:
        blockchains = json.loads(file.read())
    try:
        waly.join_blockchain_from_zip(
            blockchains["member_blockchain"],
            os.path.join(appdata_path, "member_blockchain.zip")
        )
    except waly.BlockchainAlreadyExistsError:
        pass
    try:
        waly.join_blockchain_from_zip(
            blockchains["person_blockchain"],
            os.path.join(appdata_path, "person_blockchain.zip")
        )
    except waly.BlockchainAlreadyExistsError:
        pass

    pytest.group_did_manager = GroupDidManager(appdata_path, key)


def test_cleanup():
    pytest.private_blockchain.delete()


def test_generic_blockchain_features():
    pytest.private_blockchain = test_generic_blockchain(
        PrivateBlockchain, blockchain_identity=pytest.group_did_manager)


def run_tests():
    test_preparations()
    test_generic_blockchain_features()
    test_cleanup()


if __name__ == "__main__":
    run_tests()
