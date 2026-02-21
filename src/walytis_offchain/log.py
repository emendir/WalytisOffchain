import logging
from logging.handlers import RotatingFileHandler
import os

from emtest.log_utils import get_app_log_dir

# Formatter
formatter = logging.Formatter(
    "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

# Console handler (INFO+)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)


# # Root logger
# logger_root = logging.getLogger()
# logger_root.setLevel(logging.DEBUG)  # Global default
# logger_root.addHandler(console_handler)
# # logger_root.addHandler(file_handler)

logger_waloff = logging.getLogger("Walytis_Offchain")
logger_waloff.setLevel(logging.DEBUG)
logger_blockstore = logging.getLogger("Waloff.BlockStore")
logger_blockstore.setLevel(logging.DEBUG)

# add console_handler if needed
if not any(type(h) == logging.StreamHandler for h in logger_waloff.handlers):
    logger_waloff.addHandler(console_handler)


file_handler = None
LOG_DIR = get_app_log_dir("WalytisOffchain", "Waly")
if LOG_DIR is None:
    logger_waloff.info("Logging to files is disabled.")
else:
    LOG_PATH = os.path.join(LOG_DIR, "WalytisOffchain.log")
    logger_waloff.info(f"Logging to {os.path.abspath(LOG_PATH)}")

    file_handler = RotatingFileHandler(
        LOG_PATH, maxBytes=5 * 1024 * 1024, backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    logger_waloff.addHandler(file_handler)
    logger_blockstore.addHandler(file_handler)
