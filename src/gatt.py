"""GATT definitions."""

from dataclasses import dataclass, field
from enum import IntEnum
from typing import Callable, TypeAlias

ReadTransform: TypeAlias = Callable[[bytearray], any]
WriteTransform: TypeAlias = Callable[[str, any], bytearray | None]


class ReadAction(IntEnum):
    """Enum for the automatic read actions to take place with characteristic"""

    UNKNOWN = 0

    NOOP = 1  # Do nothing
    INDEX = 2  # Query once when first connected
    POLL = 3  # Query regularly on a steady interval
    SUBSCRIBE = 4  # Subscribe to notifications
    AFTER_WRITE = 5  # Query after writing any value
    AFTER_NOTIFICATION = 6  # Query after receiving any notification

    # TODO: Don't add any additional read actions, instead introduce
    # a callback method so users can define their own logic.


class Property(IntEnum):
    """Enum for the different supported properties of a Characteristic"""

    UNKNOWN = 0

    READ = 1  # GATT can be read
    NOTIFY = 2  # GATT can be subscribed to
    WRITE = 3  # GATT can be written to

    # No idea what these do
    EXTENDED_PROPS = 4
    INDICATE = 5


@dataclass
class Characteristic:
    """See GATT Characteristics in the BLE specification"""

    uuid: str = ""
    name: str = ""
    properties: list[Property] = field(default_factory=list)

    read_action: ReadAction = ReadAction.NOOP
    read_transform: ReadTransform = lambda a: a

    write_transform: WriteTransform = lambda _a, _b: None


@dataclass
class Service:
    """See GATT Services in the BLE specification"""

    uuid: str = ""
    name: str = ""
    characteristics: list[Characteristic] = field(default_factory=list)


@dataclass
class Gatt:
    """See GATT in the BLE specification"""

    services: list[Service] = field(default_factory=list)
