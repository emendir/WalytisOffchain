from termcolor import colored as coloured
import _testing_utils
import os

import walytis_offchain
import pytest
import walytis_identities
import walytis_beta_embedded._walytis_beta.walytis_beta_api as waly
from _testing_utils import mark, test_threads_cleanup
from prebuilt_group_did_managers import (
    load_did_manager,
)
from priblocks_docker.priblocks_docker import (
    PriBlocksDocker,
    delete_containers,
)
from time import sleep
from walytis_offchain import PrivateBlockchain
from walytis_identities.utils import logger

if not _testing_utils.WE_ARE_IN_DOCKER:
    _testing_utils.assert_is_loaded_from_source(
        source_dir=os.path.dirname(os.path.dirname(__file__)),
        module=walytis_offchain
    )
    _testing_utils.assert_is_loaded_from_source(
        source_dir=os.path.join(
            os.path.abspath(
                __file__), "..", "..", "..", "walytis_identities", "src"
        ),
        module=walytis_identities
    )


print(coloured(
    "Ensure GroupDidManager tar files were created with the same IPFS node "
    "used for this test",
    "yellow"
))

waly.log.PRINT_DEBUG = False


REBUILD_DOCKER = True
DOCKER_NAME = "priblock_sync_test"

# automatically remove all docker containers after failed tests
DELETE_ALL_BRENTHY_DOCKERS = True
if _testing_utils.WE_ARE_IN_DOCKER:
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
    if _testing_utils.WE_ARE_IN_DOCKER:
        tarfile = "group_did_manager_1.tar"
    else:
        tarfile = "group_did_manager_2.tar"
    pytest.group_did_manager = load_did_manager(os.path.join(
        os.path.dirname(__file__),
        tarfile
    ))

    # in docker, update the MemberJoiningBlock to include the new
    if _testing_utils.WE_ARE_IN_DOCKER:
        logger.debug("Updating MemberJoiningBlock")
        pytest.group_did_manager.add_member(
            pytest.group_did_manager.member_did_manager)


def test_create_docker_containers():
    for i in range(1):
        pytest.containers.append(PriBlocksDocker(
            container_name=f"{DOCKER_NAME}_{i}"))


def cleanup():
    for container in pytest.containers:
        container.delete()

    pytest.group_did_manager.terminate()
    if pytest.group_did_manager:
        pytest.group_did_manager.delete()
    if pytest.pri_blockchain:
        pytest.pri_blockchain.delete()


HELLO_THERE = "Hello there!".encode()
HI = "Hi!".encode()


def test_load_blockchain():
    """Test that we can create a PrivateBlockchain and add a block."""
    logger.debug("Creating private blockchain...")
    pytest.pri_blockchain = PrivateBlockchain(pytest.group_did_manager)
    mark(True,
         "Created private blockchain"
         )


def test_add_block():
    block = pytest.pri_blockchain.add_block(HELLO_THERE)
    blockchain_blocks = list(pytest.pri_blockchain.get_blocks())
    mark(
        blockchain_blocks and
        blockchain_blocks[-1].content == block.content == HELLO_THERE,
        "Added block"
    )


def test_block_synchronisation():
    """Test that the previously created block is available in the container."""
    python_code = f'''
import sys
sys.path.insert(0, '/opt/walytis_identities/src')
sys.path.insert(0, '/opt/PriBlocks/src')
sys.path.insert(0, '/opt/PriBlocks/tests')
import _testing_utils # load walytis and IPFS properly
from walytis_offchain import PrivateBlockchain
import test_block_sharing
import walytis_beta_embedded._walytis_beta.walytis_beta_api as waly
import threading
from time import sleep
from walytis_identities.utils import logger

import test_block_sharing
from test_block_sharing import pytest
logger.debug("About to run preparations...")
logger.debug(threading.enumerate())

test_block_sharing.test_preparations()
logger.debug("About to create Private Blockchain...")
logger.debug(threading.enumerate())
pytest.pri_blockchain = PrivateBlockchain(pytest.group_did_manager)

logger.debug("Created PrivateBlockchain.")
logger.debug(threading.enumerate())
block = pytest.pri_blockchain.add_block("{HI.decode()}".encode())
logger.debug("Added private block:")
logger.debug(block.content)
sleep({SYNC_DUR})

pytest.pri_blockchain.terminate()
logger.debug("Terminated private blockchain.")
pytest.group_did_manager.terminate()
pytest.group_did_manager.member_did_manager.terminate()
# test_block_sharing.cleanup()
logger.debug("Finished cleanup.")
while len(threading.enumerate()) > 1:
    logger.debug(threading.enumerate())
    sleep(1)
'''
    pytest.containers[0].run_python_code(
        python_code, print_output=True, background=False)

    mark(
        pytest.pri_blockchain.get_num_blocks(
        ) > 0 and pytest.pri_blockchain.get_block(-1).content == HI,
        "Synchronised block"
    )


SYNC_DUR = 30


def run_tests():
    logger.debug("\nRunning tests for Private Block Sharing:")
    test_preparations()
    test_create_docker_containers()
    test_load_blockchain()

    test_add_block()
    test_block_synchronisation()
    cleanup()
    test_threads_cleanup()


if __name__ == "__main__":
    _testing_utils.PYTEST = False
    _testing_utils.BREAKPOINTS = True
    run_tests()
    _testing_utils.terminate()
