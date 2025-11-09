"""Platform for sensor integration."""

from __future__ import annotations

import logging
from collections.abc import Callable


from homeassistant.components.switch import (
    SwitchDeviceClass,
    SwitchEntityDescription,
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
)
from .src.callable_entity import (
    CallableSwitch,
    CallableDescription,
    TURN_OFF,
    TURN_ON,
    Action,
)

from .const import DOMAIN


_LOGGER = logging.getLogger(__name__)


def _write_fn(activity: str) -> list[Action]:
    if activity == TURN_ON:
        return []  # TODO
    if activity == TURN_OFF:
        return []  # TODO

    raise ValueError(f"Cannot handle activity of type {activity} as a switch.")


def _make_pump_switch(index: int) -> CallableDescription:
    """Make a pump sensor, index is 1 based."""

    return CallableDescription(
        entity_description=SwitchEntityDescription(
            key=f"FORCE_ON_ZONE_{index}", device_class=SwitchDeviceClass.SWITCH
        ),
        exists_fn=lambda data: data.get(ZONE_COUNT, 6) >= index,
        value_fn=lambda data: False,  # TODO
        write_fn=_write_fn,
    )


_SWITCHES: tuple[CallableDescription, ...] = [
    # Pumps
    _make_pump_switch(1),
    _make_pump_switch(2),
    _make_pump_switch(3),
    _make_pump_switch(4),
    _make_pump_switch(5),
    _make_pump_switch(6),
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: TacoConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up switch based on a config entry."""
    _LOGGER.debug("Setting up Taco switches: %s", entry)

    taco_runtime_data = entry.runtime_data
    update_coordinator = taco_runtime_data.update_coordinator
    data = update_coordinator.data

    # Note, we aren't actually guaranteed to have any
    # data at this point so read that value with caution!
    #
    # Home Assistant doesn't like it when we try to wait
    # for the data, or throw ConfigEntryNotReady exceptions.

    async_add_entities(
        CallableSwitch(
            update_coordinator,
            description,
            name=description.entity_description.key,
            unique_id=create_entity_id(entry, description),
            device_info=create_device_info(DOMAIN, entry),
        )
        for description in _SWITCHES
        if description.exists_fn(data)
    )
