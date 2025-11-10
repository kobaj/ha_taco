"""Data Update Coordinator for the Home Assistant Taco integration."""

from __future__ import annotations

import logging
import asyncio

from dataclasses import dataclass
from datetime import timedelta, datetime
from typing import Callable, Protocol

from bleak.backends.device import BLEDevice
from bleak import BleakClient
from bleak_retry_connector import establish_connection, BleakClientWithServiceCache

from homeassistant.core import HomeAssistant, callback

from .gatt import Gatt, Characteristic, Property, ReadAction

_LOGGER = logging.getLogger(__name__)

DEFAULT_AFTER_WRITE_INTERVAL = timedelta(seconds=30)
DEFAULT_UPDATE_INTERVAL = timedelta(seconds=5)


class _GattReadResult(Protocol):
    """The transformed result of a gatt characteristic read."""

    @property
    def key(self) -> str:
        """The key to be used in the data returned from this UpdateCoordinator."""

    @property
    def value(self) -> any:
        """The value to be used in the data returned from this UpdateCoordinator."""


@dataclass
class LocalGattReadResult:
    """Implementation for gatt read result."""

    key: str
    value: any


# TODO should probably use a proper protocol class instead of the current "pair" we are using as an argument for activity and actions.


async def _write_gatt(
    client: BleakClient,
    characteristic: Characteristic,
    bytez: bytearray | None,
) -> None:
    """Send the client a write gatt request for the characteristic."""

    await client.write_gatt_char(characteristic.uuid, bytez)
    await asyncio.sleep(0.1)  # 100 milliseconds


async def _read_gatt(
    client: BleakClient, characteristic: Characteristic, handler: Callable
) -> _GattReadResult:
    """Send the client a read gatt request for the characteristic."""

    bytez = await client.read_gatt_char(characteristic.uuid)
    transformed_result = characteristic.read_transform(bytez)
    await handler(transformed_result)


async def _setup_notification_subscriptions(
    client: BleakClient, characteristic: Characteristic, handler: Callable
) -> None:
    """Sets up and listens to gatt notifications for the characteristic."""

    async def handle_notification(_: any, data: bytearray):
        transformed_result = characteristic.read_transform(data)
        await handler(transformed_result)

    await client.start_notify(characteristic.uuid, handle_notification)


class BleDataUpdateCoordinator:
    """Utility methods for a DataUpdateCoordinator."""

    # Should probably attempt to use an ActiveBluetoothDataUpdateCoordinator
    # scheme in the future instead of the raw DataUpdateCoordinator. Since
    # it contains a bluetooth device already for us and a few other niceties.

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

        self._successful_write_time = datetime.now()

        self.update_interval = DEFAULT_UPDATE_INTERVAL

    async def _consume_result(self, result: _GattReadResult) -> None:
        """Add new incoming data to our current results."""

        if not result or not hasattr(result, "key") or not hasattr(result, "value"):
            _LOGGER.warning(
                "Rejected non GattReadResult, make sure to use a gatt transform: %s",
                result,
            )
            return

        _LOGGER.debug("Updating gatt results with: %s", result)

        async with self._results_lock:
            self._results[result.key] = result.value

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
                    self.force_data_clear()
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
        await self.force_data_update()

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
    async def poll(self, is_first_poll: bool = False) -> None:
        """Poll the device."""
        _LOGGER.debug("Polling for new data for device %s", self._ble_device.address)

        client = await self._make_client()
        try:
            poll_gatt_characteristics = [
                characteristic
                for service in self._gatt.services
                for characteristic in service.characteristics
                if Property.READ in characteristic.properties
                and (
                    (characteristic.read_action != ReadAction.NOOP and is_first_poll)
                    or (
                        characteristic.read_action == ReadAction.AFTER_WRITE
                        and (datetime.now() - self._successful_write_time)
                        < DEFAULT_AFTER_WRITE_INTERVAL
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
            return self._results.copy()

    @callback
    async def write(self, actions: list[(str, any)]) -> None:
        """Write to the device."""

        _LOGGER.debug("Writing data to device %s", self._ble_device.address)

        successful_write = False
        client = await self._make_client()
        try:
            write_gatt_characteristics = [
                characteristic
                for service in self._gatt.services
                for characteristic in service.characteristics
                if Property.WRITE in characteristic.properties
            ]

            for action_key, action_value in actions:
                for characteristic in write_gatt_characteristics:
                    bytez = characteristic.write_transform(action_key, action_value)
                    if not bytez:
                        continue

                    # The actions are deliberately a list and thus
                    # must be processed in order and synchronously.

                    await _write_gatt(client, characteristic, bytez)
                    successful_write = True
        except:
            _LOGGER.exception(
                "Failed to write data to device %s", self._ble_device.address
            )
            raise

        if successful_write:
            self._successful_write_time = datetime.now()

    async def force_data_update(self) -> None:
        """Set a timestamp so that home assistant thinks there is new data."""
        await self._consume_result(
            LocalGattReadResult("setup_timestamp", datetime.now())
        )

    async def force_data_clear(self) -> None:
        """Remove all result data."""
        async with self._results_lock:
            self._results = {}

    async def shutdown(self) -> None:
        """Stop all clients and shutdown bluetooth connections."""
        async with self._client_lock:
            if self._client and self._client.is_connected:
                self._client.disconnect()
        self.force_data_clear()
