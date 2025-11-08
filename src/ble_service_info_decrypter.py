"""Bluetooth Advertisment Device Data for Home Assistant Taco integration."""

from __future__ import annotations

import logging
from home_assistant_bluetooth import BluetoothServiceInfo
from bluetooth_data_tools import short_address


_LOGGER = logging.getLogger(__name__)


class BleServiceInfoDecrypter:
    """Class for reading information out of BluetoothServiceInfo."""

    def __init__(self, manufacturer_id:int , service_ids: list[int]):
        self._manufacturer_id = manufacturer_id
        self._service_ids = service_ids

    def is_valid_device(self, service_info: BluetoothServiceInfo) -> bool:
        """Update from BLE advertisement data."""
        _LOGGER.debug(
            "Parsing BLE advertisement data for address: %s",
            service_info.device.address,
        )

        if self._manufacturer_id not in service_info.manufacturer_data:
            return False

        service_uuids = service_info.service_uuids
        if not service_uuids:
            # The service uuids may not be set if this is the first time we are
            # connecting to and interrogating a device, so just assume its safe.
            return True

        for service_id in self._service_ids:
            if service_id not in service_uuids:
                return False

        return True


    def get_device_name(self, service_info: BluetoothServiceInfo) -> str:
        """Returns the device name built out of the model and make."""
        _LOGGER.debug(
            "Parsing BLE manufacturer data: %s",
            service_info.manufacturer_data,
        )

        return f"{service_info.name} {short_address(service_info.device.address)}"
