"""ReadTransforms and WriteTransforms for the GATT characteristics."""

from dataclasses import dataclass

import logging

_LOGGER = logging.getLogger(__name__)


@dataclass
class ReadResult:
    """The transformed result of a gatt characteristic read."""

    key: str
    value: any


def _is_byte_match(byte, target) -> bool:
    return (byte & target) == target


def _assert_bytearray_len(bytez: bytearray, length: int):
    if len(bytez) < length:
        raise ValueError(
            f"Invalid byte array, expected length of at least {length}, got ({len(bytez)}): {" ".join(f'{b:03}' for b in list(bytez))}"
        )


# Zones are only public so the taco_gatt_write_transform
# has access. Do not use these otherwise.

ZONE1 = "ZONE1"
ZONE2 = "ZONE2"
ZONE3 = "ZONE3"
ZONE4 = "ZONE4"
ZONE5 = "ZONE5"
ZONE6 = "ZONE6"

ZONE_BY_BYTE = {
    1: ZONE1,
    2: ZONE2,
    4: ZONE3,
    8: ZONE4,
    16: ZONE5,
    32: ZONE6,
}

BYTE_BY_ZONE = {v: k for k, v in ZONE_BY_BYTE.items()}

TACO_PRODUCT_INFO = "taco_product_info"


@dataclass
class TacoProductInfo:
    """All of the information about a Taco Product."""

    manufacturer: str
    family: str
    product: str  # Mostly called "id" in the Taco app
    revision: int


def read_product_id_transform(bytez: bytearray) -> ReadResult:
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

    return ReadResult(
        TACO_PRODUCT_INFO,
        TacoProductInfo(
            manufacturer.get("name", "UNKNOWN"),
            family.get("name", "UNKNOWN"),
            product,
            revision=bytez[4],
        ),
    )


ZONE_COUNT = "network_zone_count"


def read_network_zone_count_transform(bytez: bytearray) -> ReadResult:
    """Converts a bytearray to an int."""
    _assert_bytearray_len(bytez, 20)

    # Not sure why they needed 20 bytes for this...
    return ReadResult(ZONE_COUNT, bytez[19])


THERMOSTAT_INPUT_STATUS = "thermostat_input_status"


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


def read_network_thermostat_input_status_transform(
    bytez: bytearray,
) -> ReadResult:
    """Converts a bytearray to an array where each index is a zone, true means on."""
    _assert_bytearray_len(bytez, 20)

    byte = bytez[19]
    zone1 = _is_byte_match(byte, BYTE_BY_ZONE[ZONE1])
    zone2 = _is_byte_match(byte, BYTE_BY_ZONE[ZONE2])
    zone3 = _is_byte_match(byte, BYTE_BY_ZONE[ZONE3])
    zone4 = _is_byte_match(byte, BYTE_BY_ZONE[ZONE4])
    zone5 = _is_byte_match(byte, BYTE_BY_ZONE[ZONE5])
    zone6 = _is_byte_match(byte, BYTE_BY_ZONE[ZONE6])

    return ReadResult(
        THERMOSTAT_INPUT_STATUS,
        ZoneInfo(zone1, zone2, zone3, zone4, zone5, zone6),
    )


ZONE_STATUS = "zone_status"


def read_network_zone_status_transform(bytez: bytearray) -> ReadResult:
    """Converts a bytearray to an array where each index is a zone, true means on."""

    _assert_bytearray_len(bytez, 20)

    byte = bytez[19]
    zone1 = _is_byte_match(byte, BYTE_BY_ZONE[ZONE1])
    zone2 = _is_byte_match(byte, BYTE_BY_ZONE[ZONE2])
    zone3 = _is_byte_match(byte, BYTE_BY_ZONE[ZONE3])
    zone4 = _is_byte_match(byte, BYTE_BY_ZONE[ZONE4])
    zone5 = _is_byte_match(byte, BYTE_BY_ZONE[ZONE5])
    zone6 = _is_byte_match(byte, BYTE_BY_ZONE[ZONE6])

    return ReadResult(ZONE_STATUS, ZoneInfo(zone1, zone2, zone3, zone4, zone5, zone6))


NETWORK_DIAGNOSTIC_ONBOARD_INPUTS = "network_diagnostic_onboard_inputs"
NETWORK_DIAGNOSTIC_DAUGHTER_CARD = "network_diagnostic_daughter_card"
NETWORK_DIAGNOSTIC_OPERATING_MODE = "network_diagnostic_operating_mode"
NETWORK_DIAGNOSTIC_FORCE_ZONE_STATUS = "network_diagnostic_force_zone_status"
NETWORK_DIAGNOSTIC_LAST_EXCEPTION = "network_diagnostic_last_exception"


def read_network_diagnostic_data_transform(bytez: bytearray) -> ReadResult | None:
    """Reads the network diagnostic data."""

    _assert_bytearray_len(bytez, 20)

    if bytez[0] == 0 and bytez[1] == 0:
        return ReadResult("empty_network_diagnostic_data", "noop")

    if bytez[0] == 1 and bytez[1] == 0:
        return ReadResult(NETWORK_DIAGNOSTIC_ONBOARD_INPUTS, "TODO")

    if bytez[0] == 4 and bytez[1] == 0:
        return ReadResult(NETWORK_DIAGNOSTIC_DAUGHTER_CARD, "TODO")

    if bytez[0] == 16 and bytez[1] == 0:
        return ReadResult(NETWORK_DIAGNOSTIC_OPERATING_MODE, "TODO")

    if bytez[0] == 0 and bytez[1] == 16:
        # Read force zone status
        byte = bytez[3]
        zone1 = _is_byte_match(byte, BYTE_BY_ZONE[ZONE1])
        zone2 = _is_byte_match(byte, BYTE_BY_ZONE[ZONE2])
        zone3 = _is_byte_match(byte, BYTE_BY_ZONE[ZONE3])
        zone4 = _is_byte_match(byte, BYTE_BY_ZONE[ZONE4])
        zone5 = _is_byte_match(byte, BYTE_BY_ZONE[ZONE5])
        zone6 = _is_byte_match(byte, BYTE_BY_ZONE[ZONE6])
        return ReadResult(
            NETWORK_DIAGNOSTIC_FORCE_ZONE_STATUS,
            ZoneInfo(zone1, zone2, zone3, zone4, zone5, zone6),
        )

    if bytez[0] == 00 and bytez[1] == 32:
        return ReadResult(NETWORK_DIAGNOSTIC_LAST_EXCEPTION, bytez)

    _LOGGER.warning("Unknown diagnostic data bytes %s", bytez)
    return None


def read_log_transform(bytez: bytearray) -> None:
    """Reads and log data and do nothing else."""

    _LOGGER.info("Logging read of bytes %s", " ".join(f"{b:03}" for b in list(bytez)))
    return None


NETWORK_AUX1 = "network_aux1"


def read_network_aux1_transform(bytez: bytearray) -> ReadResult:
    """Converts a bytearray to an boolean."""
    _assert_bytearray_len(bytez, 2)

    # 1 means on means true
    return ReadResult(NETWORK_AUX1, _is_byte_match(bytez[1], 1))


NETWORK_AUX2 = "network_aux2"


def read_network_aux2_transform(bytez: bytearray) -> ReadResult:
    """Converts a bytearray to an boolean."""
    _assert_bytearray_len(bytez, 2)

    # 1 means on means true
    return ReadResult(NETWORK_AUX2, _is_byte_match(bytez[1], 1))


NETWORK_DEVICE_INDEX = "network_device_index"


def read_network_device_index_transform(bytez: bytearray) -> ReadResult:
    """Does nothing with the bytearray since we just write it back out again."""

    return ReadResult(NETWORK_DEVICE_INDEX, bytez)
