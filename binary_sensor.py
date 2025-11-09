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

_SENSORS: tuple[CallableSensorDescription, ...] = [
    CallableSensorDescription(
        entity_description=BinarySensorEntityDescription(
            key="ZONE1",
            device_class=BinarySensorDeviceClass.RUNNING,
        ),
        exists_fn=lambda data: data.get(ZONE_COUNT, 6) >= 1,
        value_fn=lambda data: data[ZONE_STATUS].zone1,
    ),
    CallableSensorDescription(
        entity_description=BinarySensorEntityDescription(
            key="ZONE2",
            device_class=BinarySensorDeviceClass.RUNNING,
        ),
        exists_fn=lambda data: data.get(ZONE_COUNT, 6) >= 2,
        value_fn=lambda data: data[ZONE_STATUS].zone2,
    ),
    CallableSensorDescription(
        entity_description=BinarySensorEntityDescription(
            key="ZONE3",
            device_class=BinarySensorDeviceClass.RUNNING,
        ),
        exists_fn=lambda data: data.get(ZONE_COUNT, 6) >= 3,
        value_fn=lambda data: data[ZONE_STATUS].zone3,
    ),
    CallableSensorDescription(
        entity_description=BinarySensorEntityDescription(
            key="ZONE4",
            device_class=BinarySensorDeviceClass.RUNNING,
        ),
        exists_fn=lambda data: data.get(ZONE_COUNT, 6) >= 4,
        value_fn=lambda data: data[ZONE_STATUS].zon4,
    ),
    CallableSensorDescription(
        entity_description=BinarySensorEntityDescription(
            key="ZONE5",
            device_class=BinarySensorDeviceClass.RUNNING,
        ),
        exists_fn=lambda data: data.get(ZONE_COUNT, 6) >= 5,
        value_fn=lambda data: data[ZONE_STATUS].zone5,
    ),
    CallableSensorDescription(
        entity_description=BinarySensorEntityDescription(
            key="ZONE6",
            device_class=BinarySensorDeviceClass.RUNNING,
        ),
        exists_fn=lambda data: data.get(ZONE_COUNT, 6) >= 6,
        value_fn=lambda data: data[ZONE_STATUS].zone6,
    ),
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
