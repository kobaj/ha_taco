"""Data Update Coordinator for the Home Assistant Taco integration."""

from __future__ import annotations

import logging
import asyncio

from datetime import timedelta
from typing import Callable
from dataclasses import dataclass

from bleak.backends.device import BLEDevice

from bleak import BleakClient

from bleak_retry_connector import establish_connection, BleakClientWithServiceCache

from homeassistant.core import HomeAssistant, callback

from .gatt import Gatt, Characteristic, Property, ReadAction

_LOGGER = logging.getLogger(__name__)

DEFAULT_SCAN_INTERVAL = 5  # seconds


@dataclass
class PollGattResult:
    """See GATT Characteristics in the BLE specification."""

    uuid: str
    result: any


async def _read_gatt(
    client: BleakClient, characteristic: Characteristic, handler: Callable
) -> PollGattResult:
    """Send the client a read gatt request for the characteristic."""

    data = await client.read_gatt_char(characteristic.uuid)
    transformed_result = characteristic.read_transform(data)
    gatt_result = PollGattResult(characteristic.uuid, transformed_result)
    await handler(gatt_result)


async def _setup_notification_subscriptions(
    client: BleakClient, characteristic: Characteristic, handler: Callable
) -> None:
    """Sets up and listens to gatt notifications for the characteristic."""

    async def handle_notification(_: any, data: bytearray):
        transformed_result = characteristic.read_transform(data)
        gatt_result = PollGattResult(characteristic.uuid, transformed_result)
        await handler(gatt_result)

    await client.start_notify(characteristic.uuid, handle_notification)


class BleDataUpdateCoordinator:
    """Utility methods for a ActiveBluetoothDataUpdateCoordinator."""

    def __init__(
        self,
        hass: HomeAssistant,
        ble_device: BLEDevice,
        gatt: Gatt,
    ):
        self._hass = hass
        self._ble_device = ble_device
        self._gatt = gatt

        self._results_lock = asyncio.Lock()
        self._results = {}

        self._client_lock = asyncio.Lock()
        self._client = None

        self.update_interval = timedelta(seconds=DEFAULT_SCAN_INTERVAL)

    async def _consume_result(self, result: PollGattResult) -> None:
        """Add new incoming data to our current results."""

        async with self._results_lock:
            self._results[result.uuid] = result

    async def _make_client(self) -> BleakClient:
        async with self._client_lock:
            if not self._client or not self._client.is_connected:
                try:
                    self._client = await establish_connection(
                        BleakClientWithServiceCache,
                        self._ble_device,
                        self._ble_device.address,
                    )
                except:
                    _LOGGER.exception(
                        "Failed to setup ble client for device %s",
                        self._ble_device.address,
                    )
                    raise
        # Outside of the client_lock is okay!
        return self._client

    @callback
    async def setup(self) -> None:
        """Initialize a client and establish subscriptions."""
        client = await self._make_client()
        try:
            notification_gatt_characteristics = [
                characteristic
                for service in self._gatt.services
                for characteristic in service.characteristics
                if Property.NOTIFY in characteristic.properties
                and characteristic.read_action == ReadAction.SUBSCRIBE
            ]

            poll_gatt_calls = [
                _setup_notification_subscriptions(
                    client, characteristic, self._consume_result
                )
                for characteristic in notification_gatt_characteristics
            ]

            await asyncio.gather(*poll_gatt_calls)
            await self.poll(is_first_poll=True)
        except:
            _LOGGER.exception(
                "Failed to setup notifications for device %s", self._ble_device.address
            )
            raise

    @callback
    async def poll(self, is_first_poll: bool = False):
        """Poll the device."""
        _LOGGER.debug("poll request!")

        client = await self._make_client()
        try:
            poll_gatt_characteristics = [
                characteristic
                for service in self._gatt.services
                for characteristic in service.characteristics
                if Property.READ in characteristic.properties
                and (
                    (characteristic.read_action == ReadAction.INDEX and is_first_poll)
                    or (
                        characteristic.read_action == ReadAction.SUBSCRIBE
                        and is_first_poll
                    )
                    or (characteristic.read_action == ReadAction.POLL)
                )
            ]
            poll_gatt_calls = [
                _read_gatt(client, characteristic, self._consume_result)
                for characteristic in poll_gatt_characteristics
            ]

            await asyncio.gather(*poll_gatt_calls)
        except:
            _LOGGER.exception("Failed to poll device %s", self._ble_device.address)
            raise

        async with self._results_lock:
            _LOGGER.debug("read gatt results: %s", self._results)
            return self._results

    async def shutdown(self) -> None:
        """Stop all clients and shutdown bluetooth connections."""
        async with self._client_lock:
            if self._client and self._client.is_connected:
                self._client.disconnect()
