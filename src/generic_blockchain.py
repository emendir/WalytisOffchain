"""Interface/acstract class definition for blockchain and block objects."""

from abc import ABC, abstractmethod, abstractproperty

from typing import Callable


class Block(ABC):

    @abstractproperty
    def ipfs_cid():
        pass

    @abstractproperty
    def short_id():
        pass

    @abstractproperty
    def long_id():
        pass

    @abstractproperty
    def creator_id():
        pass

    @abstractproperty
    def creation_time():
        pass

    @abstractproperty
    def topics():
        pass

    @abstractproperty
    def content_length():
        pass

    @abstractproperty
    def content_hash_algorithm():
        pass

    @abstractproperty
    def content_hash():
        pass

    @abstractproperty
    def content():
        pass

    @abstractproperty
    def n_parents():
        pass

    @abstractproperty
    def parents_hash_algorithm():
        pass

    @abstractproperty
    def parents_hash():
        pass

    @abstractproperty
    def parents():
        pass

    @abstractproperty
    def file_data():
        pass

    @abstractproperty
    def genesis():
        pass

    @abstractproperty
    def blockchain_version():
        pass


class Blockchain(ABC):
    @abstractproperty
    def blockchain_id():
        pass

    @abstractproperty
    def name():
        pass

    @abstractproperty
    def app_name():
        pass

    @abstractproperty
    def block_received_handler():
        pass

    @abstractproperty
    def block_ids():
        pass

    @abstractmethod
    def __init__(
        self,
        blockchain_id: str,
        block_received_handler: Callable[[Block], None] | None = None,
        app_name: str = "",
        appdata_dir: str = "",
        auto_load_missed_blocks: bool = True,
        forget_appdata: bool = False,
        sequential_block_handling: bool = True,
        update_blockids_before_handling: bool = False,
    ):
        pass

    @abstractmethod
    def add_block(
        self, content: bytes, topics: list[str] | str | None = None
    ) -> Block:
        pass

    @abstractmethod
    def get_block(self, id: bytes) -> Block:
        pass

    @abstractmethod
    def get_peers(self) -> list[str]:
        pass

    @abstractmethod
    def terminate(self) -> None:
        pass

    @abstractmethod
    def delete(self) -> None:
        pass
