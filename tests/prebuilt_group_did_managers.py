import os
import shutil
import tarfile
import tempfile
from datetime import datetime

import walytis_beta_embedded._walytis_beta.walytis_beta_api as waly
from walidentity.did_manager import (
    KEYSTORE_DID,
    DidManager,
    blockchain_id_from_did,
)
from walidentity.did_objects import Key
from walidentity.group_did_manager import GroupDidManager
from walidentity.key_store import KeyStore

config_dir_1 = tempfile.mkdtemp()
config_dir_2 = tempfile.mkdtemp()
CRYPTO_FAMILY = "EC-secp256k1"

private_key = '984f4581356d5d5c69f8461ae96ec300e0bf74d5e43050751d4f3ce92d0aeee7'
public_key = '04736e3bfcadc1ca5b099e566003f92a1f04379c5b626ab62a52aaf85bc3a14f2c782a9961a946bc7e72f99952b00bab52fe10f9b7dfd45fc01d551b74dd7eb94b'

key = Key(
    CRYPTO_FAMILY, public_key=public_key, private_key=private_key,
    creation_time=datetime(2024, 11, 9, 8, 30, 58, 719382)
)


def create_tar_from_directory(source_dir, tar_path):
    """Create a tar file from the source directory, placing its contents in the root of the tar file.

    Parameters:
    source_dir (str): The directory to be archived.
    tar_path (str): The path where the tar file will be saved.
    """
    with tarfile.open(tar_path, "w:gz") as tar:
        # Iterate through all the files and directories in the source directory
        for root, dirs, files in os.walk(source_dir):
            for file in files:
                file_path = os.path.join(root, file)
                # Calculate the relative path to store in the tar file
                arcname = os.path.relpath(file_path, start=source_dir)
                tar.add(file_path, arcname=arcname)
            for dir in dirs:
                dir_path = os.path.join(root, dir)
                arcname = os.path.relpath(dir_path, start=source_dir)
                tar.add(dir_path, arcname=arcname)


def extract_tar_to_directory(tar_path, dest_dir):
    """Extract a tar file to the destination directory.

    Parameters:
    tar_path (str): The path to the tar file.
    dest_dir (str): The directory where the tar contents will be extracted.
    """
    with tarfile.open(tar_path, "r:gz") as tar:
        tar.extractall(path=dest_dir)


def create_did_managers():
    print("Creating DidManagers...")
    member_1_keystore = KeyStore(
        os.path.join(config_dir_1, "member_keys.json"), key
    )
    member_2_keystore = KeyStore(
        os.path.join(config_dir_2, "member_keys.json"), key
    )

    member_1_did_manager = DidManager.create(member_1_keystore)
    member_2_did_manager = DidManager.create(member_2_keystore)

    group_1_keystore = KeyStore(
        os.path.join(config_dir_1, "group_keys.json"), key
    )
    group_2_keystore = KeyStore(
        os.path.join(config_dir_2, "group_keys.json"), key
    )
    group_did_manager_1 = GroupDidManager.create(
        group_1_keystore, member_1_did_manager
    )
    invitation = group_did_manager_1.invite_member()
    group_did_manager_2 = GroupDidManager.join(
        invitation, group_2_keystore, member_2_did_manager
    )
    group_did_manager_2.unlock(
        group_did_manager_1.get_control_key().private_key
    )
    print("Unlocked joined GroupDidManager instance.")

    shutil.copy(
        group_did_manager_1.blockchain.get_blockchain_data(),
        os.path.join(config_dir_1, "group_blockchain.zip")
    )
    shutil.copy(
        group_did_manager_1.member_did_manager.blockchain.get_blockchain_data(),
        os.path.join(config_dir_1, "member_blockchain.zip")
    )

    shutil.copy(
        group_did_manager_2.blockchain.get_blockchain_data(),
        os.path.join(config_dir_2, "group_blockchain.zip")
    )
    shutil.copy(
        group_did_manager_2.member_did_manager.blockchain.get_blockchain_data(),
        os.path.join(config_dir_2, "member_blockchain.zip")
    )
    group_did_manager_1.terminate()
    group_did_manager_2.terminate()
    # Create the tar file
    create_tar_from_directory(config_dir_1, "group_did_manager_1.tar")
    create_tar_from_directory(config_dir_2, "group_did_manager_2.tar")
    print("Created appdata tar files.")


def load_did_manager(tarfile:str):
    """Load some of the """
    appdata_path = tempfile.mkdtemp()
    
    extract_tar_to_directory(tarfile,appdata_path)

    # join the group_did_manager' blockchains
    group_keystore = KeyStore(os.path.join(
        appdata_path, "group_keys.json"), key)
    member_keystore = KeyStore(os.path.join(
        appdata_path, "member_keys.json"), key)
    group_blockchain_id = blockchain_id_from_did(
        group_keystore.get_custom_metadata()[KEYSTORE_DID]
    )
    member_blockchain_id = blockchain_id_from_did(
        member_keystore.get_custom_metadata()[KEYSTORE_DID]
    )

    try:
        waly.join_blockchain_from_zip(
            member_blockchain_id,
            os.path.join(appdata_path, "member_blockchain.zip")
        )
    except waly.BlockchainAlreadyExistsError:
        pass
    try:
        waly.join_blockchain_from_zip(
            group_blockchain_id,
            os.path.join(appdata_path, "group_blockchain.zip")
        )
    except waly.BlockchainAlreadyExistsError:
        pass

    return GroupDidManager(group_keystore, member_keystore)


if __name__ == "__main__":
    create_did_managers()
