"""ReadTransforms and WriteTransforms for the GATT characteristics."""

from dataclasses import dataclass

import logging

from .ble_data_update_coordinator import GattReadResult


_LOGGER = logging.getLogger(__name__)

_ZONE1 = "ZONE1"
_ZONE2 = "ZONE2"
_ZONE3 = "ZONE3"
_ZONE4 = "ZONE4"
_ZONE5 = "ZONE5"
_ZONE6 = "ZONE6"

_ZONE_BY_BYTE = {
    1: _ZONE1,
    2: _ZONE2,
    4: _ZONE3,
    8: _ZONE4,
    16: _ZONE5,
    32: _ZONE6,
}

_BYTE_BY_ZONE = {v: k for k, v in _ZONE_BY_BYTE.items()}


def _is_byte_match(byte, target) -> bool:
    return (byte & target) == target


def _assert_bytearray_len(bytez: bytearray, length: int):
    if len(bytez) != length:
        raise ValueError(
            f"Invalid byte array, expected length of {length}, got: {bytes}"
        )


def write_password_transform(password: str) -> bytearray:
    """Converts a password string to a bytearray."""

    if len(password) > 20:
        raise ValueError("Cannot have a TACO password more than 20 characters.")
    return bytearray(string=password, encoding="ascii")


TACO_PRODUCT_INFO = "tacoProductInfo"


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

    return GattReadResult(
        TACO_PRODUCT_INFO,
        TacoProductInfo(
            manufacturer.get("name", "UNKNOWN"),
            family.get("name", "UNKNOWN"),
            product,
            revision=bytez[4],
        ),
    )


ZONE_COUNT = "networkZoneCount"


def read_network_zone_count_transform(bytez: bytearray) -> int:
    """Converts a bytearray to an int."""
    _assert_bytearray_len(bytez, 20)

    # Not sure why they needed 20 bytes for this...
    return GattReadResult(ZONE_COUNT, bytez[19])


THERMOSTAT_INPUT_STATUS = "thermostatInputStatus"


@dataclass
class ZoneInfo:
    """All of the information about the zones"""

    # True means on.
    zone1: bool
    zone2: bool
    zone3: bool
    zone4: bool
    zone5: bool
    zone6: bool

    def get_zone(self, index: int) -> bool | None:
        """Returns the zone value at index, 1 based."""

        if index == 1:
            return self.zone1
        if index == 2:
            return self.zone2
        if index == 3:
            return self.zone3
        if index == 4:
            return self.zone4
        if index == 5:
            return self.zone5
        if index == 6:
            return self.zone6
        return None


def read_network_thermostat_input_status_transform(
    bytez: bytearray,
) -> ZoneInfo:
    """Converts a bytearray to an array where each index is a zone, true means on."""
    _assert_bytearray_len(bytez, 20)

    byte = bytez[19]
    zone1 = _is_byte_match(byte, _BYTE_BY_ZONE[_ZONE1])
    zone2 = _is_byte_match(byte, _BYTE_BY_ZONE[_ZONE2])
    zone3 = _is_byte_match(byte, _BYTE_BY_ZONE[_ZONE3])
    zone4 = _is_byte_match(byte, _BYTE_BY_ZONE[_ZONE4])
    zone5 = _is_byte_match(byte, _BYTE_BY_ZONE[_ZONE5])
    zone6 = _is_byte_match(byte, _BYTE_BY_ZONE[_ZONE6])

    return GattReadResult(
        THERMOSTAT_INPUT_STATUS,
        ZoneInfo(zone1, zone2, zone3, zone4, zone5, zone6),
    )


ZONE_STATUS = "zoneStatus"


def read_network_zone_status_transform(bytez: bytearray) -> ZoneInfo:
    """Converts a bytearray to an array where each index is a zone, true means on."""

    _assert_bytearray_len(bytez, 20)

    byte = bytez[19]
    zone1 = _is_byte_match(byte, _BYTE_BY_ZONE[_ZONE1])
    zone2 = _is_byte_match(byte, _BYTE_BY_ZONE[_ZONE2])
    zone3 = _is_byte_match(byte, _BYTE_BY_ZONE[_ZONE3])
    zone4 = _is_byte_match(byte, _BYTE_BY_ZONE[_ZONE4])
    zone5 = _is_byte_match(byte, _BYTE_BY_ZONE[_ZONE5])
    zone6 = _is_byte_match(byte, _BYTE_BY_ZONE[_ZONE6])

    return GattReadResult(
        ZONE_STATUS, ZoneInfo(zone1, zone2, zone3, zone4, zone5, zone6)
    )
