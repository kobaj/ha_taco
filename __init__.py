"""Package for Home Assistant Taco Integration."""

from __future__ import annotations

import logging

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.components import bluetooth
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from bleak_retry_connector import close_stale_connections_by_address

from .src.taco_init import setup_write_loop, send_initial_write_requests
from .src.ble_data_update_coordinator import BleDataUpdateCoordinator
from .src.taco_config_entry import TacoConfigEntry, TacoRuntimeData
from .src.ble_config_flow import BLE_CONF_DEVICE_ADDRESS


from .const import DOMAIN, taco_gatt
from .config_flow import CONF_TACO_DEVICE_PASSWORD


_LOGGER = logging.getLogger(__name__)


PLATFORMS: list[Platform] = [Platform.BINARY_SENSOR, Platform.SWITCH]

# TODO add RSSI as a sensor


async def async_setup_entry(hass: HomeAssistant, entry: TacoConfigEntry) -> bool:
    """Set up device from a config entry."""
    _LOGGER.info("Setting up a Taco!: %s with data %s", entry, entry.data)

    hass.data.setdefault(DOMAIN, {})

    address = entry.data.get(BLE_CONF_DEVICE_ADDRESS)
    assert address
    await close_stale_connections_by_address(address)

    # Start bluetooth setup.
    ble_device = bluetooth.async_ble_device_from_address(
        hass, address.upper(), connectable=True
    )
    if not ble_device:
        raise ConfigEntryNotReady(
            translation_domain=DOMAIN,
            translation_key="device_not_found_error",
            translation_placeholders={"address": address},
        )

    # Start our data coordinators, responsible for reading/writing bluetooth data.
    #
    # Store these and other important info in runtime_data so
    # sensors and other entities can access it.
    ble_coordinator = BleDataUpdateCoordinator(hass, ble_device, taco_gatt)
    update_coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=DOMAIN,
        update_method=ble_coordinator.poll,
        setup_method=ble_coordinator.setup,
        update_interval=ble_coordinator.update_interval,
        always_update=False,
    )
    entry.runtime_data = TacoRuntimeData(
        address=address,
        password=entry.data.get(CONF_TACO_DEVICE_PASSWORD),
        update_coordinator=update_coordinator,
        ble_coordinator=ble_coordinator,
    )

    # Very important Taco setup.
    await send_initial_write_requests(entry.runtime_data)
    entry.runtime_data.remove_listeners = await setup_write_loop(
        hass, entry.runtime_data
    )

    # Need to get data now because some of the entry setup will use it.
    await update_coordinator.async_config_entry_first_refresh()

    # Subscribe entries.
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Trigger a force read for all the entrys that just subscribed.
    await ble_coordinator.force_data_update()

    return True


async def async_unload_entry(hass: HomeAssistant, entry: TacoConfigEntry) -> bool:
    """Unload a config entry."""
    await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    await entry.runtime_data.remove_listeners()
    await entry.runtime_data.ble_coordinator.shutdown()  # private, meh.

    return True
