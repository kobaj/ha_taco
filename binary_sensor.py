"""Platform for sensor integration."""

from __future__ import annotations

import logging

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntityDescription,
)

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import (
    AddConfigEntryEntitiesCallback,
)

from .src.taco_config_entry import TacoConfigEntry
from .src.taco_device_info import create_device_info, create_entity_id
from .src.taco_gatt_read_transform import (
    THERMOSTAT_INPUT_STATUS,
    ZONE_STATUS,
    ZONE_COUNT,
    ZoneInfo,
    NETWORK_AUX1,
    NETWORK_AUX2,
)
from .src.callable_entity import CallableBinarySensor, CallableDescription

from .const import DOMAIN


_LOGGER = logging.getLogger(__name__)


def _value_fn(data: dict[str, any], key: str, index: int):
    """Returns the zone value at index, 1 based."""
    value = data.get(key, None)
    if not value:
        return None

    return getattr(value, f"zone{index}")


def _make_zone_sensor(index: int) -> CallableDescription:
    """Make a zone sensor, index is 1 based."""

    return CallableDescription(
        entity_description=BinarySensorEntityDescription(
            key=f"ZONE_{index}",
            device_class=BinarySensorDeviceClass.RUNNING,
        ),
        exists_fn=lambda data: data.get(ZONE_COUNT, 6) >= index,
        value_fn=lambda data: _value_fn(data, ZONE_STATUS, index),
    )


def _make_thermostat_sensor(index: int) -> CallableDescription:
    """Make a zone sensor, index is 1 based."""

    return CallableDescription(
        entity_description=BinarySensorEntityDescription(
            key=f"THERMOSTAT_{index}",
            device_class=None,  # Deliberately none
        ),
        exists_fn=lambda data: data.get(ZONE_COUNT, 6) >= index,
        value_fn=lambda data: _value_fn(data, THERMOSTAT_INPUT_STATUS, index),
    )


def _make_aux_sensor(index: int) -> CallableDescription:
    """Make an aux sensor, index is 1 based."""

    key = {
        1: NETWORK_AUX1,
        2: NETWORK_AUX2,
    }.get(index, None)

    return CallableDescription(
        entity_description=BinarySensorEntityDescription(
            key=f"AUX_{index}",
            device_class=BinarySensorDeviceClass.RUNNING,
        ),
        exists_fn=lambda _data: True,
        value_fn=lambda data: data.get(key, None),
    )


_SENSORS: tuple[CallableDescription, ...] = [
    # Pumps
    _make_zone_sensor(1),
    _make_zone_sensor(2),
    _make_zone_sensor(3),
    _make_zone_sensor(4),
    _make_zone_sensor(5),
    _make_zone_sensor(6),
    # Thermostats
    _make_thermostat_sensor(1),
    _make_thermostat_sensor(2),
    _make_thermostat_sensor(3),
    _make_thermostat_sensor(4),
    _make_thermostat_sensor(5),
    _make_thermostat_sensor(6),
    # Aux
    # Don't enable these, they don't work. See comment inside of const.py
    # _make_aux_sensor(1),
    # _make_aux_sensor(2),
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
            unique_id=create_entity_id(entry, description),
            device_info=create_device_info(DOMAIN, entry),
        )
        for description in _SENSORS
        if description.exists_fn(data)
    )
