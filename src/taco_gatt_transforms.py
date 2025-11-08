"""ReadTransforms and WriteTransforms for the GATT characteristics."""

from dataclasses import dataclass, field

import logging


_LOGGER = logging.getLogger(__name__)

ZONE1 = "ZONE1"
ZONE2 = "ZONE2"
ZONE3 = "ZONE3"
ZONE4 = "ZONE4"
ZONE5 = "ZONE5"
ZONE6 = "ZONE6"

ZONE_BY_BYTE = {
   1 : ZONE1,
   2 : ZONE2,
   4 : ZONE3,
   8 : ZONE4,
   16: ZONE5,
   32: ZONE6,
}

BYTE_BY_ZONE = { v: k for k, v in ZONE_BY_BYTE.items() }


def _is_byte_match(byte, target) -> bool:
    return (byte & target) == target

def _assert_bytearray_len(bytez: bytearray, length: int):
    if len(bytez) != length:
        raise ValueError(f"Invalid byte array, expected length of {length}, got: {bytes}")


def write_password_transform(password: str) -> bytearray:
    """Converts a password string to a bytearray."""

    if len(password) > 20:
        raise ValueError("Cannot have a TACO password more than 20 characters.")
    return bytearray(string=password, encoding="ascii")


@dataclass
class TacoProductInfo:
    """All of the information about a Taco Product."""

    manufacturer: str
    family: str
    product: str  # Mostly called "id" in the Taco app
    revision: int


def read_product_id_transform(bytez: bytearray) -> TacoProductInfo:
    """Converts a bytearray to a TacoProductInfo."""
    _assert_bytearray_len(bytez, 5)

    # Despite being called "byByte", the key is actually an int.
    manufacturer_by_byte = {
        1: {
            "name": "TACO",
            1: {"name": "LEAK_BREAKER"},
            16: {
                "name": "SR",
                18: "SR502",
                19: "SR503",
                20: "SR504",
                21: "SR505",
                22: "SR506",
            },
            17: {
                "name": "ZVC",
                19: "ZVC503",
                20: "ZVC504",
                21: "ZVC505",
                22: "ZVC506",
            },
            18: {"name": "CIRCULATOR"},
        }
    }

    manufacturer = manufacturer_by_byte.get(bytez[0], {})
    family = manufacturer.get(bytez[1], {})
    product = family.get(bytez[2], "UNKNOWN")

    return TacoProductInfo(
        manufacturer.get("name", "UNKNOWN"),
        family.get("name", "UNKNOWN"),
        product,
        revision=bytez[4],
    )

def read_network_zone_count_transform(bytez: bytearray) -> int:
    """Converts a bytearray to an int."""
    _assert_bytearray_len(bytez, 20)

    # Not sure why they needed 20 bytes for this...
    return bytez[19]

def read_network_thermostat_input_status_transform(bytez: bytearray) -> [int]:
    """Converts a bytearray to an array where each index is a zone, true means on."""
    _assert_bytearray_len(bytez, 20)

    byte = bytez[19]
    zone1 = _is_byte_match(byte, ZONE_BY_BYTE[ZONE1])
    zone2 = _is_byte_match(byte, ZONE_BY_BYTE[ZONE2])
    zone3 = _is_byte_match(byte, ZONE_BY_BYTE[ZONE3])
    zone4 = _is_byte_match(byte, ZONE_BY_BYTE[ZONE4])
    zone5 = _is_byte_match(byte, ZONE_BY_BYTE[ZONE5])
    zone6 = _is_byte_match(byte, ZONE_BY_BYTE[ZONE6])

    return [zone1, zone2, zone3, zone4, zone5, zone6]

def read_network_zone_status_transform(bytez: bytearray) -> [int]:
    """Converts a bytearray to an array where each index is a zone, true means on."""

    _assert_bytearray_len(bytez, 20)

    byte = bytez[19]
    zone1 = _is_byte_match(byte, ZONE_BY_BYTE[ZONE1])
    zone2 = _is_byte_match(byte, ZONE_BY_BYTE[ZONE2])
    zone3 = _is_byte_match(byte, ZONE_BY_BYTE[ZONE3])
    zone4 = _is_byte_match(byte, ZONE_BY_BYTE[ZONE4])
    zone5 = _is_byte_match(byte, ZONE_BY_BYTE[ZONE5])
    zone6 = _is_byte_match(byte, ZONE_BY_BYTE[ZONE6])

    return [zone1, zone2, zone3, zone4, zone5, zone6]