"""Script for configuring tests.

Runs automatically when pytest runs a test before loading the test module.
"""

import threading
import time
import logging
from emtest import assert_is_loaded_from_source
from emtest import set_env_var
from loguru import logger
from walytis_beta_tools._experimental.config import (
    WalytisTestModes,
    get_walytis_test_mode,
)
import os
import sys

import pytest
from emtest import (
    add_path_to_python,
    are_we_in_docker,
    configure_pytest_reporter,
)

PRINT_ERRORS = (
    True  # whether or not to print error messages after failed tests
)

WORKDIR = os.path.dirname(os.path.abspath(__file__))
PROJ_DIR = os.path.dirname(WORKDIR)
SRC_DIR = os.path.join(PROJ_DIR, "src")

os.chdir(WORKDIR)

# add source code paths to python's search paths
add_path_to_python(SRC_DIR)


@pytest.hookimpl(trylast=True)
def pytest_configure(config):
    """Make changes to pytest's behaviour."""
    configure_pytest_reporter(config, print_errors=PRINT_ERRORS)

    terminal = config.pluginmanager.get_plugin("terminalreporter")
    if terminal:
        terminal.write_line(f"Python {sys.version.split(' ')[0]}")


def pytest_sessionfinish(
    session: pytest.Session,
    exitstatus: pytest.ExitCode,
) -> None:
    """Clean up after pytest has finished."""
    os._exit(int(exitstatus))  # force close terminating dangling threads


if True:
    # Walytis Config: use Brenthy by default if not otherwise specified by env var
    if are_we_in_docker():
        os.environ["USE_IPFS_NODE"] = "false"
        os.environ["WALYTIS_BETA_API_TYPE"] = "WALYTIS_BETA_BRENTHY_API"
    set_env_var(
        "WALYTIS_BETA_API_TYPE", "WALYTIS_BETA_BRENTHY_API", override=False
    )

    set_env_var(
        "WALYTIS_BETA_LOG_PATH",
        os.path.join(os.getcwd(), "Walytis.log"),
        override=True,
    )
    from walytis_beta_tools._experimental.ipfs_interface import ipfs
    import walytis_beta_embedded
    import walytis_beta_api
    from brenthy_tools_beta import BrenthyNotRunningError
    import walytis_offchain
    from brenthy_tools_beta import brenthy_api

    def assert_brenthy_online(timeout: int = 2) -> None:
        """Check if Brenthy is reachable, raising an error if not."""
        brenthy_api.get_brenthy_version(timeout=timeout)

    # walytis_beta_tools.log.logger_blockchain_model.setLevel(logging.DEBUG)
    # walytis_beta_tools.log.file_handler.setLevel(logging.DEBUG)
    USING_BRENTHY = (
        walytis_beta_api.walytis_beta_interface.get_walytis_beta_api_type()
        == walytis_beta_api.walytis_beta_interface.WalytisBetaApiTypes.WALYTIS_BETA_BRENTHY_API
    )
    logger.info(f"USING BRENTHY: {USING_BRENTHY}")
    if USING_BRENTHY:
        while True:
            try:
                assert_brenthy_online()
                break
            except BrenthyNotRunningError as e:
                logger.error(e)
                logger.info("Retrying to connect to brenthy...")
    else:
        walytis_beta_embedded.set_appdata_dir("./.blockchains")
        walytis_beta_embedded.run_blockchains()
    print("IPFS Peer ID:", ipfs.peer_id)
    import walytis_identities

    if not are_we_in_docker():
        assert_is_loaded_from_source(SRC_DIR, walytis_offchain)
    walytis_identities.log.console_handler.setLevel(logging.DEBUG)
    walytis_offchain.log.console_handler.setLevel(logging.DEBUG)
    walytis_beta_embedded.set_appdata_dir("./.blockchains")

    os.environ["PRIVATE_BLOCKS_DATA_DIR"] = os.path.join(WORKDIR, ".waloff")

    from walytis_offchain.log import file_handler, console_handler, formatter

    file_handler.setLevel(logging.DEBUG)
    console_handler.setLevel(logging.DEBUG)

    # add logging for IPFS-Toolkit
    from ipfs_tk_transmission.log import logger_transm, logger_conv
    from emtest.log_utils import get_app_log_dir

    file_handler_ipfs = logging.handlers.RotatingFileHandler(
        os.path.join(get_app_log_dir("IPFS_TK", "Waly"), "IPFS_TK.log"),
        maxBytes=5 * 1024 * 1024,
        backupCount=5,
    )
    file_handler_ipfs.setLevel(logging.DEBUG)
    file_handler_ipfs.setFormatter(formatter)
    logger_transm.addHandler(file_handler_ipfs)
    logger_conv.addHandler(file_handler_ipfs)
    logger_conv.setLevel(logging.DEBUG)
    logger_transm.setLevel(logging.DEBUG)

    disabled_loggers = ["urllib3.connectionpool"]
    for logger_name in disabled_loggers:
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.WARNING)
