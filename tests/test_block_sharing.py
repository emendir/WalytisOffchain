import testing_utils
import tempfile
import walytis_beta_api as walytis_beta_api
import pytest
import sys
import os
from testing_utils import mark, polite_wait
from priblocks_docker.priblocks_docker import (
    PriBlocksDocker, delete_containers
)
import json
from multi_crypt import Crypt
import shutil

walytis_beta_api.log.PRINT_DEBUG = False

if True:
    sys.path.insert(0, os.path.join(
        os.path.abspath(os.path.dirname(os.path.dirname(__file__))),
    ))
    sys.path.insert(0, os.path.join(
        os.path.abspath(os.path.dirname(os.path.dirname(__file__))), "..", "WalytisAuth", "src"
    ))
    from private_blockchain import PrivateBlockchain
    from identity.did_objects import Key
    from identity.key_store import KeyStore
    from identity.identity import IdentityAccess
    from identity.did_manager import DidManager
    from identity.utils import logger
REBUILD_DOCKER = True

# automatically remove all docker containers after failed tests
DELETE_ALL_BRENTHY_DOCKERS = True


def test_preparations():
    if DELETE_ALL_BRENTHY_DOCKERS:
        delete_containers(image="local/priblocks_testing")

    if REBUILD_DOCKER:
        from priblocks_docker.build_docker import build_docker_image

        build_docker_image(verbose=False)
    pytest.member_1 = None
    pytest.member_2 = None
    pytest.member_1_config_dir = tempfile.mkdtemp()
    pytest.member_2_config_dir = tempfile.mkdtemp()
    pytest.key_store_path = os.path.join(
        pytest.member_1_config_dir, "keystore.json")

    # the cryptographic family to use for the tests
    pytest.CRYPTO_FAMILY = "EC-secp256k1"
    pytest.CRYPT = Crypt(
        pytest.CRYPTO_FAMILY, b"\'\n%\xa3\xca\x0c\xc9\x97\xfd\xb3D$\x16\x06\xebrv\xc2\xb2\x15\'\xc5\xc1\x04\xe7\xf6i\xf4\xd53W\xc7")
    pytest.containers: list[PriBlocksDocker] = []
    pytest.invitation = None


def test_create_docker_containers():
    for i in range(1):
        pytest.containers.append(PriBlocksDocker())


def cleanup():
    for container in pytest.containers:
        container.delete()
    if pytest.member_2:
        pytest.member_2.terminate()
        pytest.member_2.member_did_manager.delete()
    if pytest.member_1:
        pytest.member_1.delete()
    shutil.rmtree(pytest.member_1_config_dir)
    shutil.rmtree(pytest.member_2_config_dir)


def create_identity_and_invitation():
    """Create an identity and invitation for it.

    TO BE RUN IN DOCKER CONTAINER.
    """
    logger.debug("DockerTest: creating identity...")
    pytest.member_1 = IdentityAccess.create(
        "/opt",
        pytest.CRYPT,
    )
    logger.debug("DockerTest: creating invitation...")
    invitation = pytest.member_1.invite_member()
    print(json.dumps(invitation))
    # mark(isinstance(pytest.member_1, IdentityAccess), "Created IdentityAccess")


def check_new_member(did: str):
    """Add a new member to pytest.member_1.

    TO BE RUN IN DOCKER CONTAINER.
    """
    logger.debug("CND: Loading IdentityAccess...")
    pytest.member_1 = IdentityAccess.load_from_appdata(
        "/opt",
        pytest.CRYPT,
    )

    # pytest.member_1.add_member(
    #     did,
    #     invitation
    # )

    logger.debug("CND: Getting members...")
    members = pytest.member_1.get_members()
    success = (
        did in [
            member["did"]
            for member in pytest.member_1.person_did_manager.get_members()
        ]
        and did in [
            member["did"]
            for member in pytest.member_1.get_members()
        ]
    )
    logger.debug("CND: got data, exiting...")

    if success:
        print(success)
    else:
        print("\nDocker: DID-MAnager Members:\n",
              pytest.member_1.person_did_manager.get_members())
        print("\nDocker: Person Members:\n", pytest.member_1.get_members())


def test_create_identity_and_invitation():
    print("Creating identiy and invitation on docker...")
    python_code = "\n".join([
        "import sys;",
        "sys.path.append('/opt/PriBlocks/tests');",
        "import test_block_sharing;",
        "test_block_sharing.REBUILD_DOCKER=False;",
        "test_block_sharing.DELETE_ALL_BRENTHY_DOCKERS=False;",
        "test_block_sharing.test_preparations();",
        "test_block_sharing.create_identity_and_invitation();",
        "test_block_sharing.pytest.member_1.terminate()",
        # "test_block_sharing.cleanup()"
    ])
    output = None
    # print(python_code)
    # breakpoint()
    output = pytest.containers[0].run_python_code(
        python_code, print_output=False
    )
    # print("Got output!")
    # print(output)
    try:
        pytest.invitation = json.loads(output.split("\n")[-1])
    except:
        print(f"\n{python_code}\n")
        pass
    mark(
        pytest.invitation is not None,
        "created identity and invitation on docker"
    )


def test_add_member_identity():
    try:
        pytest.member_2 = IdentityAccess.join(
            pytest.invitation, pytest.member_2_config_dir, pytest.CRYPT)
    except walytis_beta_api.JoinFailureError:
        try:
            pytest.member_2 = IdentityAccess.join(
                pytest.invitation, pytest.member_2_config_dir, pytest.CRYPT)
        except walytis_beta_api.JoinFailureError as error:
            print(error)
            breakpoint()
    pytest.member_2_did = pytest.member_2.member_did_manager.get_did()

    # wait a short amount to allow the docker container to learn of the new member
    polite_wait(2)

    print("Adding member on docker...")
    wait_dur_s = 60
    python_code = (
        "import sys;"
        "from time import sleep;"
        "from loguru import logger;"
        "sys.path.append('/opt/PriBlocks/tests');"
        "import test_block_sharing;"
        "test_block_sharing.REBUILD_DOCKER=False;"
        "test_block_sharing.DELETE_ALL_BRENTHY_DOCKERS=False;"
        "test_block_sharing.test_preparations();"
        f"test_block_sharing.check_new_member('{pytest.member_2_did}');"
        f"[(sleep(10), logger.debug('waiting...')) for i in range({wait_dur_s//10})];"
        "test_block_sharing.pytest.member_1.terminate();"
        "test_block_sharing.cleanup();"
        "logger.debug('Done!');"
        "import threading;"
        "logger.debug(str(threading.enumerate()));"
        "import sys;"
        "sys.exit();"
    )
    # breakpoint()
    pytest.containers[0].run_python_code(
        python_code, print_output=False, background=True
    )
    # print("Waiting for key sharing...")
    polite_wait(wait_dur_s)
    mark(
        pytest.member_2.person_did_manager.get_control_key().private_key,
        "New member got control key ownership"
    )


HELLO_THERE = "Hello there!".encode()


def test_add_block():
    pytest.blockchain_id = walytis_beta_api.create_blockchain()
    pytest.pri_blockchain = PrivateBlockchain(
        pytest.member_2, walytis_beta_api.Blockchain, pytest.blockchain_id
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

    test_create_identity_and_invitation()
    if not pytest.invitation:
        print("Skipped remaining tests because first test failed.")
        cleanup()
        return
    test_add_member_identity()
    test_add_block()
    cleanup()


if __name__ == "__main__":
    testing_utils.PYTEST = False
    testing_utils.BREAKPOINTS = True
    run_tests()
