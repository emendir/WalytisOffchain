import json
import os
import tempfile

import _testing_utils
import identity
import private_blockchain
import pytest
import walytis_beta_api as waly
from _testing_utils import mark, test_threads_cleanup
from identity.identity import IdentityAccess
from priblocks_docker.create_test_identity import (
    extract_tar_to_directory,
    key,
)
from priblocks_docker.priblocks_docker import (
    PriBlocksDocker,
    delete_containers,
)
from private_blockchain import PrivateBlockchain

_testing_utils.assert_is_loaded_from_source(
    source_dir=os.path.dirname(os.path.dirname(__file__)), module=private_blockchain
)
_testing_utils.assert_is_loaded_from_source(
    source_dir=os.path.join(os.path.abspath(__file__), "..", "..", "..", "WalytisAuth", "src"), module=identity
)

waly.log.PRINT_DEBUG = False


REBUILD_DOCKER = True

# automatically remove all docker containers after failed tests
DELETE_ALL_BRENTHY_DOCKERS = True
if os.path.exists("/opt/we_are_in_docker"):
    REBUILD_DOCKER = False
    DELETE_ALL_BRENTHY_DOCKERS = False


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
    if os.path.exists("/opt/we_are_in_docker"):
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

    pytest.identity_access = IdentityAccess.load_from_appdata(
        appdata_path, key)


def test_create_docker_containers():
    for i in range(1):
        pytest.containers.append(PriBlocksDocker())


def cleanup():
    for container in pytest.containers:
        container.delete()

    pytest.identity_access.terminate()
    if pytest.identity_access:
        pytest.identity_access.delete()
    if pytest.pri_blockchain:
        pytest.pri_blockchain.delete()


HELLO_THERE = "Hello there!".encode()


def test_add_block():
    """Test that we can create a PrivateBlockchain and add a block."""
    print("Creating private blockchain...")
    pytest.blockchain_id = waly.create_blockchain()
    pytest.pri_blockchain = PrivateBlockchain(pytest.identity_access)
    block = pytest.pri_blockchain.add_block(HELLO_THERE)
    mark(
        pytest.pri_blockchain.get_blocks(
        )[-1].private_content == block.private_content == HELLO_THERE,
        "Created private blockchain, added block"
    )


def test_block_synchronisation():
    """Test that the previously created block is available in the container."""
    python_code = '''
import sys
sys.path.insert(0, '/opt/WalytisAuth/src')
sys.path.insert(0, '/opt/PriBlocks/src')
sys.path.insert(0, '/opt/PriBlocks/tests')
from private_blockchain import PrivateBlockchain
import test_block_sharing
import walytis_beta_api as waly
from test_block_sharing import pytest
print("About to run preparations...")
test_block_sharing.test_preparations()
print("About to create Private Blockchain...")
pytest.pri_blockchain = PrivateBlockchain(pytest.identity_access)
print("Created PrivateBlockchain.")
block = pytest.pri_blockchain.add_block("Hello there!".encode())
print(block.private_content)
pytest.pri_blockchain.terminate()
print("Terminated private blockchain.")
pytest.identity_access.terminate()
# test_block_sharing.cleanup()
print("Finished cleanup.")
import threading
from time import sleep
while len(threading.enumerate()) > 1:
    print(threading.enumerate())
    sleep(1)
print(threading.enumerate())
'''
    output = pytest.containers[0].run_python_code(python_code)
    # breakpoint()
    mark(
        HELLO_THERE.decode() in output,
        "Synchronised block"
    )


def run_tests():
    print("\nRunning tests for Key Sharing:")
    test_preparations()
    test_create_docker_containers()

    test_add_block()
    test_block_synchronisation()
    cleanup()
    test_threads_cleanup()


if __name__ == "__main__":
    _testing_utils.PYTEST = False
    _testing_utils.BREAKPOINTS = True
    run_tests()
