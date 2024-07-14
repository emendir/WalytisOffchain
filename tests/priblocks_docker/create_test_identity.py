import shutil
import tarfile
import os
from identity.identity import IdentityAccess
from identity.did_objects import Key
import tempfile
from datetime import datetime
config_dir_1 = tempfile.mkdtemp()
config_dir_2 = tempfile.mkdtemp()
CRYPTO_FAMILY = "EC-secp256k1"

private_key = '984f4581356d5d5c69f8461ae96ec300e0bf74d5e43050751d4f3ce92d0aeee7'
public_key = '04736e3bfcadc1ca5b099e566003f92a1f04379c5b626ab62a52aaf85bc3a14f2c782a9961a946bc7e72f99952b00bab52fe10f9b7dfd45fc01d551b74dd7eb94b'

key = Key(
    CRYPTO_FAMILY, public_key=public_key, private_key=private_key,
    creation_time=datetime.now()
)


def create_tar_from_directory(source_dir, tar_path):
    """
    Create a tar file from the source directory, placing its contents in the root of the tar file.

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
    """
    Extract a tar file to the destination directory.

    Parameters:
    tar_path (str): The path to the tar file.
    dest_dir (str): The directory where the tar contents will be extracted.
    """
    with tarfile.open(tar_path, "r:gz") as tar:
        tar.extractall(path=dest_dir)


def run():
    identity_access_1 = IdentityAccess.create(config_dir_1, key)
    invitation = identity_access_1.invite_member()
    identity_access_2 = IdentityAccess.join(invitation, config_dir_2, key)
    identity_access_2.person_did_manager.unlock(
        identity_access_1.person_did_manager.get_control_key().private_key
    )
    print("Unlocked PersonIdentity on joined access.")

    shutil.copy(
        identity_access_1.person_did_manager.blockchain.get_blockchain_data(),
        os.path.join(config_dir_1, "person_blockchain.zip")
    )
    shutil.copy(
        identity_access_1.member_did_manager.blockchain.get_blockchain_data(),
        os.path.join(config_dir_1, "member_blockchain.zip")
    )

    shutil.copy(
        identity_access_2.person_did_manager.blockchain.get_blockchain_data(),
        os.path.join(config_dir_2, "person_blockchain.zip")
    )
    shutil.copy(
        identity_access_2.member_did_manager.blockchain.get_blockchain_data(),
        os.path.join(config_dir_2, "member_blockchain.zip")
    )

    # Create the tar file
    create_tar_from_directory(config_dir_1, "identity_access_1.tar")
    create_tar_from_directory(config_dir_2, "identity_access_2.tar")
    print("Created appdata tar files.")

    identity_access_1.terminate()
    identity_access_2.terminate()


if __name__ == "__main__":
    run()
