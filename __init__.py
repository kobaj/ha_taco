"""Package for Home Assistant Taco Integration."""

from __future__ import annotations

import logging


from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.components import bluetooth
from homeassistant.exceptions import ConfigEntryNotReady

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from bleak_retry_connector import close_stale_connections_by_address

from .src.ble_data_update_coordinator import BleDataUpdateCoordinator
from .src.taco_config_entry import TacoConfigEntry, TacoRuntimeData

from .const import DOMAIN, taco_gatt
from .config_flow import CONF_TACO_DEVICE_PASSWORD


_LOGGER = logging.getLogger(__name__)

# TODO support buttons too!
PLATFORMS: list[Platform] = []


async def async_setup_entry(hass: HomeAssistant, entry: TacoConfigEntry) -> bool:
    """Set up device from a config entry."""
    _LOGGER.debug("Setting up an entry: %s", entry)

    hass.data.setdefault(DOMAIN, {})

    address = entry.unique_id
    assert address
    await close_stale_connections_by_address(address)

    device_password = entry.data.get(CONF_TACO_DEVICE_PASSWORD)
    assert device_password

    connectable = False
    ble_device = bluetooth.async_ble_device_from_address(
        hass, address.upper(), connectable=connectable
    )
    if not ble_device:
        raise ConfigEntryNotReady(
            translation_domain=DOMAIN,
            translation_key="device_not_found_error",
            translation_placeholders={"address": address},
        )

    data_coordinator = BleDataUpdateCoordinator(hass, ble_device, taco_gatt)
    update_coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=DOMAIN,
        update_method=data_coordinator.poll,
        setup_method=data_coordinator.setup,
        update_interval=data_coordinator.update_interval,
    )
    await update_coordinator.async_config_entry_first_refresh()

    entry.runtime_data = TacoRuntimeData(
        data_coordinator=data_coordinator,
        update_coordinator=update_coordinator,
    )
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: TacoConfigEntry) -> bool:
    """Unload a config entry."""
    await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    await entry.runtime_data.data_coordinator.shutdown()

    return True
