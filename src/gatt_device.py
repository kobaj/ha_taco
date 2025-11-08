"""generic bt device"""

from uuid import UUID
import asyncio
import logging
from contextlib import AsyncExitStack

from bleak import BleakClient
from bleak.exc import BleakError


_LOGGER = logging.getLogger(__name__)


# Comes from https://github.com/fuatakgun/generic_bt/blob/main/custom_components/generic_bt/generic_bt_api/device.py
class GattDevice:
    """Generic BT GATT Device Class"""
    def __init__(self, ble_device):
        self._ble_device = ble_device
        self._client: BleakClient | None = None
        self._client_stack = AsyncExitStack()
        self._lock = asyncio.Lock()

    @property
    def connected(self):
        return not self._client is None

    async def get_client(self):
        async with self._lock:
            if not self._client:
                _LOGGER.debug("Connecting")
                try:
                    self._client = await self._client_stack.enter_async_context(BleakClient(self._ble_device, timeout=30))
                except asyncio.TimeoutError as exc:
                    _LOGGER.debug("Timeout on connect", exc_info=True)
                    raise IdealLedTimeout("Timeout on connect") from exc
                except BleakError as exc:
                    _LOGGER.debug("Error on connect", exc_info=True)
                    raise IdealLedBleakError("Error on connect") from exc
            else:
                _LOGGER.debug("Connection reused")

    async def write_gatt(self, target_uuid, data):
        await self.get_client()
        uuid_str = "{" + target_uuid + "}"
        uuid = UUID(uuid_str)
        data_as_bytes = bytearray.fromhex(data)
        await self._client.write_gatt_char(uuid, data_as_bytes, True)

    async def read_gatt(self, target_uuid):
        await self.get_client()
        uuid_str = "{" + target_uuid + "}"
        uuid = UUID(uuid_str)
        data = await self._client.read_gatt_char(uuid)
        print(data)
        return data

    def update_from_advertisement(self, advertisement):
        pass