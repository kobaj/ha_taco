"""Package for Home Assistant Taco Integration."""

from __future__ import annotations

import logging


from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.components import bluetooth
from homeassistant.exceptions import ConfigEntryNotReady, ConfigEntryAuthFailed

from bleak_retry_connector import close_stale_connections_by_address

from .src.callable_entity import CallableTwoWayDataUpdateCoordinator
from .src.ble_data_update_coordinator import BleDataUpdateCoordinator
from .src.taco_config_entry import TacoConfigEntry, TacoRuntimeData
from .src.ble_config_flow import BLE_CONF_DEVICE_ADDRESS
from .src.taco_gatt_write_transform import (
    PROVIDE_PASSWORD,
    REQUEST_FORCE_ZONE_STATUS,
)

from .const import DOMAIN, taco_gatt
from .config_flow import CONF_TACO_DEVICE_PASSWORD


_LOGGER = logging.getLogger(__name__)


PLATFORMS: list[Platform] = [Platform.BINARY_SENSOR, Platform.SWITCH]


async def async_setup_entry(hass: HomeAssistant, entry: TacoConfigEntry) -> bool:
    """Set up device from a config entry."""
    _LOGGER.debug("Setting up a Taco!: %s", entry)

    hass.data.setdefault(DOMAIN, {})

    address = entry.data.get(BLE_CONF_DEVICE_ADDRESS)
    assert address
    await close_stale_connections_by_address(address)

    ble_device = bluetooth.async_ble_device_from_address(
        hass, address.upper(), connectable=True
    )
    if not ble_device:
        raise ConfigEntryNotReady(
            translation_domain=DOMAIN,
            translation_key="device_not_found_error",
            translation_placeholders={"address": address},
        )

    data_coordinator = BleDataUpdateCoordinator(hass, ble_device, taco_gatt)
    update_coordinator = CallableTwoWayDataUpdateCoordinator(
        hass,
        _LOGGER,
        name=DOMAIN,
        update_method=data_coordinator.poll,
        setup_method=data_coordinator.setup,
        write_method=data_coordinator.write,
        update_interval=data_coordinator.update_interval,
        always_update=False,
    )

    # TODO should run an authorization check and throw an reauthentication
    # exception if the current password is both set and not correct.
    # See more: https://developers.home-assistant.io/docs/config_entries_config_flow_handler/#reauthentication
    password = entry.data.get(CONF_TACO_DEVICE_PASSWORD)
    if password and len(password) > 20:
        raise ConfigEntryAuthFailed(
            "Cannot have a Taco password more than 20 characters."
        )

    # Send off an initial request to get the force zone status.
    if password:
        await update_coordinator.write(
            [
                (PROVIDE_PASSWORD, password),
                (REQUEST_FORCE_ZONE_STATUS, None),
            ]
        )

    # Need to get data now because some of the entry setup will use it.
    await update_coordinator.async_config_entry_first_refresh()

    entry.runtime_data = TacoRuntimeData(
        address=address,
        password=password,
        update_coordinator=update_coordinator,
        _data_coordinator=data_coordinator,
    )
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Trigger a force refresh for all the entrys that just subscribed.
    await data_coordinator.force_data_update()

    return True


async def async_unload_entry(hass: HomeAssistant, entry: TacoConfigEntry) -> bool:
    """Unload a config entry."""
    await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    await entry.runtime_data._data_coordinator.shutdown()  # private, meh.

    return True
