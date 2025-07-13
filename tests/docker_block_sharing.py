
from termcolor import colored as coloured
import os

import walytis_offchain
import pytest
import walytis_identities
import walytis_beta_api as waly
from prebuilt_group_did_managers import (
    load_did_manager,
)
from waloff_docker.waloff_docker import (
    PriBlocksDocker,
    delete_containers,
)
from time import sleep
from walytis_offchain import PrivateBlockchain
from loguru import logger
from walytis_offchain.log import logger_waloff as logger
import threading

SYNC_DUR = 30
class SharedData():
    pass
shared_data = SharedData()
logger.info("Initialised shared_data.")

from emtest import are_we_in_docker
def test_preparations():
    shared_data.group_did_manager = None
    shared_data.pri_blockchain = None
    shared_data.containers: list[PriBlocksDocker] = []

    # Load pre-created GroupDidManager objects for testing:

    logger.info("Loading GDMs from tar files...")
    # choose which group_did_manager to load
    tarfile = "group_did_manager_1.tar"
    shared_data.group_did_manager = load_did_manager(os.path.join(
        os.path.dirname(__file__),
        tarfile
    ))

    # in docker, update the MemberJoiningBlock to include the new
    logger.debug("Updating MemberJoiningBlock")
    shared_data.group_did_manager.add_member(
        shared_data.group_did_manager.member_did_manager)

HI = "Hi!".encode()
HELLO_THERE = "Hello there!".encode()
def docker_part():

    shared_data.pri_blockchain = PrivateBlockchain(shared_data.group_did_manager)

    logger.debug("Created PrivateBlockchain.")
    logger.debug(threading.enumerate())
    block = shared_data.pri_blockchain.add_block(HI)
    logger.debug("Added private block:")
    logger.debug(block.content)
    sleep(SYNC_DUR)

    shared_data.pri_blockchain.terminate()
    logger.debug("Terminated private blockchain.")
    shared_data.group_did_manager.terminate()
    shared_data.group_did_manager.member_did_manager.terminate()
    # test_block_sharing.cleanup()
    logger.debug("Finished cleanup.")
    while len(threading.enumerate()) > 1:
        logger.debug(threading.enumerate())
        sleep(1)
