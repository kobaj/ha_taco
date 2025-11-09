"""Platform for sensor integration."""

from __future__ import annotations

import logging
from collections.abc import Callable


from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntityDescription,
)

from homeassistant.exceptions import ConfigEntryNotReady

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import (
    AddConfigEntryEntitiesCallback,
)

from .src.taco_config_entry import TacoConfigEntry
from .src.taco_device_info import create_device_info, create_sensor_id
from .src.taco_gatt_transform import THERMOSTAT_INPUT_STATUS, ZONE_STATUS, ZONE_COUNT
from .src.callable_sensor import CallableBinarySensor, CallableSensorDescription

from .const import DOMAIN


_LOGGER = logging.getLogger(__name__)


def make_pump_sensor(index: int) -> CallableSensorDescription:
    """Make a pump sensor, index is 1 based."""

    return CallableSensorDescription(
        entity_description=BinarySensorEntityDescription(
            key=f"ZONE_{index}",
            device_class=BinarySensorDeviceClass.RUNNING,
        ),
        exists_fn=lambda data: data.get(ZONE_COUNT, 6) >= index,
        value_fn=lambda data: data[ZONE_STATUS].get_zone(index),
    )


def make_thermostat_sensor(index: int) -> CallableSensorDescription:
    """Make a pump sensor, index is 1 based."""

    return CallableSensorDescription(
        entity_description=BinarySensorEntityDescription(
            key=f"THERMOSTAT_{index}",
            device_class=None,  # Deliberately none
        ),
        exists_fn=lambda data: data.get(ZONE_COUNT, 6) >= index,
        value_fn=lambda data: data[THERMOSTAT_INPUT_STATUS].get_zone(index),
    )


_SENSORS: tuple[CallableSensorDescription, ...] = [
    # Pumps
    make_pump_sensor(1),
    make_pump_sensor(2),
    make_pump_sensor(3),
    make_pump_sensor(4),
    make_pump_sensor(5),
    make_pump_sensor(6),
    # Thermostats
    make_thermostat_sensor(1),
    make_thermostat_sensor(2),
    make_thermostat_sensor(3),
    make_thermostat_sensor(4),
    make_thermostat_sensor(5),
    make_thermostat_sensor(6),
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: TacoConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up sensor based on a config entry."""
    _LOGGER.debug("Setting up Taco binary sensors: %s", entry)

    taco_runtime_data = entry.runtime_data
    update_coordinator = taco_runtime_data.update_coordinator
    data = update_coordinator.data

    # Note, we aren't actually guaranteed to have any
    # data at this point so read that value with caution!
    #
    # Home Assistant doesn't like it when we try to wait
    # for the data, or throw ConfigEntryNotReady exceptions.

    async_add_entities(
        CallableBinarySensor(
            update_coordinator,
            description,
            name=description.entity_description.key,
            unique_id=create_sensor_id(entry, description),
            device_info=create_device_info(DOMAIN, entry),
        )
        for description in _SENSORS
        if description.exists_fn(data)
    )
