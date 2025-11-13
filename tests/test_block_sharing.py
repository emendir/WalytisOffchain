import _auto_run_with_pytest  # noqa
import logging
import os

from docker_block_sharing import HELLO_THERE, HI
from emtest import await_thread_cleanup, env_vars
from prebuilt_group_did_managers import (
    load_did_manager,
)
from termcolor import colored as coloured
from waloff_docker.waloff_docker import (
    PriBlocksDocker,
    delete_containers,
)

from walytis_offchain import PrivateBlockchain
from walytis_offchain.log import logger_waloff as logger

print(
    coloured(
        "Ensure GroupDidManager tar files were created with the same IPFS node "
        "used for this test",
        "yellow",
    )
)


REBUILD_DOCKER = True
REBUILD_DOCKER = env_vars.bool("TESTS_REBUILD_DOCKER", default=REBUILD_DOCKER)
DOCKER_NAME = "priblock_sync_test"


class SharedData:
    pass


shared_data = SharedData()
logger.info("Initialised shared_data.")


def test_preparations():
    logger.info("Deleting old docker containers...")
    delete_containers(image="local/waloff_testing")

    if REBUILD_DOCKER:
        from waloff_docker.build_docker import build_docker_image

        build_docker_image(verbose=False)
    shared_data.group_did_manager = None
    shared_data.pri_blockchain = None
    shared_data.containers: list[PriBlocksDocker] = []

    # Load pre-created GroupDidManager objects for testing:

    logger.info("Loading GDMs from tar files...")
    # choose which group_did_manager to load
    tarfile = "group_did_manager_2.tar"
    shared_data.group_did_manager = load_did_manager(
        os.path.join(os.path.dirname(__file__), tarfile)
    )


def test_create_docker_containers():
    logger.info("Creating docker containers...")
    for i in range(1):
        shared_data.containers.append(
            PriBlocksDocker(container_name=f"{DOCKER_NAME}0{i}")
        )


def cleanup():
    for container in shared_data.containers:
        container.delete()

    shared_data.group_did_manager.terminate()
    if shared_data.group_did_manager:
        shared_data.group_did_manager.delete()
    if shared_data.pri_blockchain:
        shared_data.pri_blockchain.delete()


def test_load_blockchain():
    """Test that we can create a PrivateBlockchain and add a block."""
    logger.debug("Creating private blockchain...")
    shared_data.pri_blockchain = PrivateBlockchain(
        shared_data.group_did_manager
    )
    assert True, "Created private blockchain"


def test_add_block():
    block = shared_data.pri_blockchain.add_block(HELLO_THERE)
    blockchain_blocks = list(shared_data.pri_blockchain.get_blocks())
    assert (
        blockchain_blocks
        and blockchain_blocks[-1].content == block.content == HELLO_THERE
    ), "Added block"


def test_block_synchronisation():
    """Test that the previously created block is available in the container."""
    python_code = """
import sys
sys.path.insert(0, '/opt/PriBlocks/src')
sys.path.insert(0, '/opt/PriBlocks/tests')

import conftest
from walytis_offchain import PrivateBlockchain
import docker_block_sharing
import walytis_beta_api as waly
import threading

import docker_block_sharing
from docker_block_sharing import shared_data


docker_block_sharing.test_preparations_docker()
docker_block_sharing.docker_part()
"""
    shared_data.containers[0].run_python_code(
        python_code, print_output=True, background=False
    )

    assert (
        shared_data.pri_blockchain.get_num_blocks() > 0
        and shared_data.pri_blockchain.get_block(-1).content == HI
    ), "Synchronised block"


def test_threads_cleanup() -> None:
    """Test that no threads are left running."""
    cleanup()
    assert await_thread_cleanup(timeout=5)
