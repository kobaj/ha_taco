"""ReadTransforms and WriteTransforms for the GATT characteristics."""

from dataclasses import dataclass

import logging

from .taco_gatt_read_transform import (
    ZoneInfo,
    ZONE1,
    ZONE2,
    ZONE3,
    ZONE4,
    ZONE5,
    ZONE6,
    BYTE_BY_ZONE,
)

_LOGGER = logging.getLogger(__name__)


@dataclass
class WriteRequest:
    """A write request, will be passed to write_transform as two args."""

    action: str
    extra: any


PROVIDE_PASSWORD = "provide_password"


def write_password_transform(action: str, password: str) -> bytearray | None:
    """Converts a password string to a bytearray."""

    if action != PROVIDE_PASSWORD:
        return None

    return bytearray(password, encoding="ascii")


def _write_force_zone_on(zone_info: ZoneInfo) -> bytearray:
    """Converts a zone on request to a bytearray."""

    # Yes, this is technically an integer.
    zone_byte = 0
    zone_byte |= BYTE_BY_ZONE[ZONE1] if zone_info.zone1 else 0
    zone_byte |= BYTE_BY_ZONE[ZONE2] if zone_info.zone2 else 0
    zone_byte |= BYTE_BY_ZONE[ZONE3] if zone_info.zone3 else 0
    zone_byte |= BYTE_BY_ZONE[ZONE4] if zone_info.zone4 else 0
    zone_byte |= BYTE_BY_ZONE[ZONE5] if zone_info.zone5 else 0
    zone_byte |= BYTE_BY_ZONE[ZONE6] if zone_info.zone6 else 0

    return bytearray([0, 16, 0, zone_byte])


def _write_force_zone_status_request() -> bytearray:
    """Creates a force zone status request to a bytearray."""

    # Note, there is a significant delay required between setting the force zone on
    # and then attempting to read its status with the following command.
    #
    # TODO one day I'll figure out a solution.
    return bytearray([1, 0, 0, 16])


REQUEST_FORCE_ZONE_STATUS = "request_force_zones_status"
FORCE_ZONE_ON = "force_zones_on"


def write_network_diagnostic_mode_transform(
    action: str, extra: any
) -> bytearray | None:
    """Converts extra to a network diagnostic mode bytearray."""

    if action == REQUEST_FORCE_ZONE_STATUS:
        return _write_force_zone_status_request()
    if action == FORCE_ZONE_ON:
        return _write_force_zone_on(extra)
    return None
