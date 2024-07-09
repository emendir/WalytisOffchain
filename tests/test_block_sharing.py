import json
import os
import sys
import tempfile

import pytest
import testing_utils
import walytis_beta_api as walytis_beta_api
from priblocks_docker.create_test_identity import (
    extract_tar_to_directory,
    key,
)
from priblocks_docker.priblocks_docker import (
    PriBlocksDocker,
    delete_containers,
)
from testing_utils import mark, test_threads_cleanup

walytis_beta_api.log.PRINT_DEBUG = False

if True:
    sys.path.insert(0, os.path.join(
        os.path.abspath(os.path.dirname(os.path.dirname(__file__))),
    ))
    sys.path.insert(0, os.path.join(
        os.path.abspath(os.path.dirname(os.path.dirname(__file__))), "..", "WalytisAuth", "src"
    ))
    from identity.identity import IdentityAccess

    from private_blockchain import PrivateBlockchain
REBUILD_DOCKER = True

# automatically remove all docker containers after failed tests
DELETE_ALL_BRENTHY_DOCKERS = True


def test_preparations():
    if DELETE_ALL_BRENTHY_DOCKERS:
        delete_containers(image="local/priblocks_testing")

    if REBUILD_DOCKER:
        from priblocks_docker.build_docker import build_docker_image

        build_docker_image(verbose=False)
    pytest.identity_access = None
    pytest.pri_blockchain = None
    pytest.containers: list[PriBlocksDocker] = []

    # Load pre-created IdentityAccess objects for testing:

    # choose which identity_access to load
    if os.path.exists("/opt/PriBlocks/we_are_in_docker"):
        appdata_path = "/opt/PB_TestIdentity"
    else:
        appdata_path = tempfile.mkdtemp()
        extract_tar_to_directory(
            os.path.join(
                os.path.dirname(__file__),
                "priblocks_docker",
                "identity_access_2.tar"
            ),
            appdata_path
        )

    # join the identity_access' blockchains
    with open(os.path.join(appdata_path, "person_id.json"), "r") as file:
        blockchains = json.loads(file.read())
    try:
        walytis_beta_api.join_blockchain_from_zip(
            blockchains["member_blockchain"],
            os.path.join(appdata_path, "member_blockchain.zip")
        )
    except walytis_beta_api.BlockchainAlreadyExistsError:
        pass
    try:
        walytis_beta_api.join_blockchain_from_zip(
            blockchains["person_blockchain"],
            os.path.join(appdata_path, "person_blockchain.zip")
        )
    except walytis_beta_api.BlockchainAlreadyExistsError:
        pass

    pytest.identity_access = IdentityAccess.load_from_appdata(appdata_path, key)


def test_create_docker_containers():
    for i in range(1):
        pytest.containers.append(PriBlocksDocker())


def cleanup():
    for container in pytest.containers:
        container.delete()

    if pytest.identity_access:
        pytest.identity_access.delete()
    if pytest.pri_blockchain:
        pytest.pri_blockchain.delete()


HELLO_THERE = "Hello there!".encode()


def test_add_block():
    """Test that we can create a PrivateBlockchain and add a block."""
    pytest.blockchain_id = walytis_beta_api.create_blockchain()
    pytest.pri_blockchain = PrivateBlockchain(
        pytest.identity_access, walytis_beta_api.Blockchain, pytest.blockchain_id
    )
    block = pytest.pri_blockchain.add_block(HELLO_THERE)
    mark(
        pytest.pri_blockchain.get_blocks()[-1].block_content == block.block_content == HELLO_THERE,
        "Created private blockchain, added block"
    )


def run_tests():
    print("\nRunning tests for Key Sharing:")
    test_preparations()
    test_create_docker_containers()

    test_add_block()
    test_threads_cleanup()
    cleanup()


if __name__ == "__main__":
    testing_utils.PYTEST = False
    testing_utils.BREAKPOINTS = True
    run_tests()
