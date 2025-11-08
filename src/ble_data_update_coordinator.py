"""Data Update Coordinator for the Home Assistant Taco integration."""

from __future__ import annotations

import logging
import asyncio
from contextlib import asynccontextmanager

from typing import Callable
from dataclasses import dataclass

from bleak.backends.device import BLEDevice

from bleak import BleakClient

from bleak_retry_connector import establish_connection, BleakClientWithServiceCache

from homeassistant.core import HomeAssistant, callback

from .gatt import Gatt, Characteristic, Property, ReadAction

_LOGGER = logging.getLogger(__name__)

DEFAULT_SCAN_INTERVAL = 10  # seconds


@dataclass
class _PollGattResult:
    """See GATT Characteristics in the BLE specification."""

    uuid: str
    result: any


async def _read_gatt(
    client: BleakClient, characteristic: Characteristic, handler: Callable
) -> _PollGattResult:
    """Send the client a read gatt request for the characteristic."""

    data = await client.read_gatt_char(characteristic.uuid)
    transformed_result = characteristic.read_transform(data)
    gatt_result = _PollGattResult(characteristic.uuid, transformed_result)
    await handler(gatt_result)


async def _setup_notification_subscriptions(
    client: BleakClient, characteristic: Characteristic, handler: Callable
):
    """Sets up and listens to gatt notifications for the characteristic."""

    async def handle_notification(_: any, data: bytearray):
        transformed_result = characteristic.read_transform(data)
        gatt_result = _PollGattResult(characteristic.uuid, transformed_result)
        await handler(gatt_result)

    return await client.start_notify(characteristic.uuid, handle_notification)

@asynccontextmanager
async def _make_client(ble_device: BLEDevice) -> BleakClient:
    """Generator for making a client. MUST be called as a `with` statement."""

    try:
        client = await establish_connection(
            BleakClientWithServiceCache, ble_device, ble_device.address
        )
        yield client
    finally:
        await client.disconnect()

class BleDataUpdateCoordinator:
    """Utility methods for a ActiveBluetoothDataUpdateCoordinator."""

    def __init__(
        self,
        hass: HomeAssistant,
        gatt: Gatt,
        scan_interval: int | None = None,
    ):
        self._DONT_COMMIT_THIS_VARIABLE = True
        self._results = {}
        self._lock = asyncio.Lock()

        self._hass = hass
        self._gatt = gatt
        self._scan_interval = DEFAULT_SCAN_INTERVAL
        if scan_interval:
            self._scan_interval = scan_interval

    @callback
    async def consume_result(self, result: _PollGattResult):
        """Add new incoming data to our current results."""

        async with self._lock:
            self._results[result.uuid] = result

    @callback
    async def setup(self, service_info: BluetoothServiceInfoBleak) -> None:
        """First time setup."""
        async with _make_client(service_info.device) as client:
            try:
                notification_gatt_characteristics = [
                    characteristic
                    for service in self._gatt.services
                    for characteristic in service.characteristics
                    if Property.NOTIFY in characteristic.properties
                    and (characteristic.read_action == ReadAction.SUBSCRIBE)
                ]

                poll_gatt_calls = [
                    _setup_notification_subscriptions(
                        client, characteristic, self.consume_result
                    )
                    for characteristic in notification_gatt_characteristics
                ]

                await asyncio.gather(*poll_gatt_calls)
                # DONT COMMIT
                # await self.poll(is_first_poll=True)
            except:
                _LOGGER.exception(
                    "Failed to setup notifications for device %s", service_info.device.address
                )
                raise


    @callback
    async def poll(self, service_info: BluetoothServiceInfoBleak, is_first_poll: bool=False) -> None:
        """Poll the device."""

        if self._DONT_COMMIT_THIS_VARIABLE:
            is_first_poll = True
            self._DONT_COMMIT_THIS_VARIABLE = False
            await self.setup(service_info)

        async with _make_client(service_info.device) as client:
            try:
                poll_gatt_characteristics = [
                    characteristic
                    for service in self._gatt.services
                    for characteristic in service.characteristics
                    if Property.READ in characteristic.properties
                    and (
                        characteristic.read_action == ReadAction.INDEX
                        and is_first_poll
                    )
                    or characteristic.read_action == ReadAction.POLL
                ]
                poll_gatt_calls = [
                    _read_gatt(client, characteristic, self.consume_result)
                    for characteristic in poll_gatt_characteristics
                ]

                await asyncio.gather(*poll_gatt_calls)
            except:
                _LOGGER.exception("Failed to poll device %s", service_info.device.address)
                raise

            async with self._lock:
                _LOGGER.debug("read gatt results: %s", self._results)
                return self._results
