import os

import _testing_utils
import private_blocks
import pytest
import walidentity
import walytis_beta_api as waly
from _testing_utils import mark, test_threads_cleanup
from prebuilt_group_did_managers import (
    load_did_manager,
)
from priblocks_docker.priblocks_docker import (
    PriBlocksDocker,
    delete_containers,
)
from private_blocks import PrivateBlockchain

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
    pytest.group_did_manager = None
    pytest.pri_blockchain = None
    pytest.containers: list[PriBlocksDocker] = []

    # Load pre-created GroupDidManager objects for testing:

    # choose which group_did_manager to load
    if os.path.exists("/opt/we_are_in_docker"):
        tarfile = "group_did_manager_1.tar"
    else:
        tarfile = "group_did_manager_2.tar"
    pytest.group_did_manager = load_did_manager(os.path.join(
        os.path.dirname(__file__),
        tarfile
    ))


def test_create_docker_containers():
    for i in range(1):
        pytest.containers.append(PriBlocksDocker())


def cleanup():
    for container in pytest.containers:
        container.delete()

    pytest.group_did_manager.terminate()
    if pytest.group_did_manager:
        pytest.group_did_manager.delete()
    if pytest.pri_blockchain:
        pytest.pri_blockchain.delete()


HELLO_THERE = "Hello there!".encode()


def test_add_block():
    """Test that we can create a PrivateBlockchain and add a block."""
    print("Creating private blockchain...")
    pytest.pri_blockchain = PrivateBlockchain(pytest.group_did_manager)
    block = pytest.pri_blockchain.add_block(HELLO_THERE)
    blockchain_blocks = list(pytest.pri_blockchain.get_blocks())
    mark(
        blockchain_blocks and
        blockchain_blocks[-1].content == block.content == HELLO_THERE,
        "Created private blockchain, added block"
    )


def test_block_synchronisation():
    """Test that the previously created block is available in the container."""
    python_code = '''
import sys
sys.path.insert(0, '/opt/WalIdentity/src')
sys.path.insert(0, '/opt/PriBlocks/src')
sys.path.insert(0, '/opt/PriBlocks/tests')
from private_blocks import PrivateBlockchain
import test_block_sharing
import walytis_beta_api as waly
import threading
from time import sleep

from test_block_sharing import pytest
print("About to run preparations...")
print(threading.enumerate())

test_block_sharing.test_preparations()
print("About to create Private Blockchain...")
print(threading.enumerate())
pytest.pri_blockchain = PrivateBlockchain(pytest.group_did_manager)

print("Created PrivateBlockchain.")
print(threading.enumerate())
block = pytest.pri_blockchain.add_block("Hello there!".encode())
print(block.content)

pytest.pri_blockchain.terminate()
print("Terminated private blockchain.")
pytest.group_did_manager.terminate()
pytest.group_did_manager.member_did_manager.terminate()
# test_block_sharing.cleanup()
print("Finished cleanup.")
while len(threading.enumerate()) > 1:
    print(threading.enumerate())
    sleep(1)
print(threading.enumerate())
'''
    output = pytest.containers[0].run_python_code(
        python_code, print_output=True)
    # breakpoint()
    mark(
        HELLO_THERE.decode() in output,
        "Synchronised block"
    )

from time import sleep
def run_tests():
    print("\nRunning tests for Private Block Sharing:")
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
