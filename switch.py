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

from .src.taco_config_entry import TacoConfigEntry, TacoRuntimeData
from .src.taco_device_info import create_device_info, create_entity_id
from .src.taco_gatt_read_transform import (
    ZONE_COUNT,
    NETWORK_DIAGNOSTIC_FORCE_ZONE_STATUS,
)
from .src.callable_entity import (
    CallableSwitch,
    CallableDescription,
    SWITCH_TURN_OFF,
    SWITCH_TURN_ON,
)

from .const import DOMAIN


_LOGGER = logging.getLogger(__name__)


def _value_fn(
    data: dict[str, any], index: int, taco_runtime_data: TacoRuntimeData
) -> bool | None:
    """Returns the zone value at index, 1 based."""

    # Read from internal state for remaining lifetime of entity.
    # Making a few assumptions that taco_init.py will correctly
    # match this by sending a write all force on zones to False on boot.
    #
    # TLDR, Home Assistant is the authority and source of truth for switches.
    return taco_runtime_data.force_zone_on[index - 1]


def _write_fn(
    switch_activity: str,
    data: dict[str, any],
    index: int,
    taco_runtime_data: TacoRuntimeData,
) -> None:
    """Setup the actions necessary to actuate a switch"""

    # Because of unreliability with reading the force zone status,
    # and we want home assistant to be the authority,
    # we are relying on the runtime_data internal state rather than
    # anything else to maintain the source of truth for the switch.

    if switch_activity == SWITCH_TURN_ON:
        taco_runtime_data.force_zone_on[index - 1] = True
        return

    if switch_activity == SWITCH_TURN_OFF:
        taco_runtime_data.force_zone_on[index - 1] = False
        return

    _LOGGER.info("Got an unknown switch activity: %s", switch_activity)


def _make_zone_switch(
    index: int, taco_runtime_data: TacoRuntimeData
) -> CallableDescription:
    """Make a zone sensor, index is 1 based."""

    return CallableDescription(
        entity_description=SwitchEntityDescription(
            key=f"FORCE_ON_ZONE_{index}", device_class=SwitchDeviceClass.SWITCH
        ),
        exists_fn=lambda data: data.get(ZONE_COUNT, 6) >= index,
        value_fn=lambda data: _value_fn(data, index, taco_runtime_data),
        write_fn=lambda activity, data: _write_fn(
            activity, data, index, taco_runtime_data
        ),
    )


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

    if not taco_runtime_data.password:
        _LOGGER.info(
            "No password provided to Taco, so no switches or buttons are enabled."
        )
        return

    # Note, we aren't actually guaranteed to have any
    # data at this point so read that value with caution!
    #
    # Home Assistant doesn't like it when we try to wait
    # for the data, or throw ConfigEntryNotReady exceptions.

    switches = [
        # zones
        _make_zone_switch(1, taco_runtime_data),
        _make_zone_switch(2, taco_runtime_data),
        _make_zone_switch(3, taco_runtime_data),
        _make_zone_switch(4, taco_runtime_data),
        _make_zone_switch(5, taco_runtime_data),
        _make_zone_switch(6, taco_runtime_data),
    ]

    async_add_entities(
        CallableSwitch(
            update_coordinator,
            description,
            name=description.entity_description.key,
            unique_id=create_entity_id(entry, description),
            device_info=create_device_info(DOMAIN, entry),
        )
        for description in switches
        if description.exists_fn(data)
    )
