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
    ZONE_STATUS,
    ZoneInfo,
    NETWORK_DIAGNOSTIC_FORCE_ZONE_STATUS,
)
from .src.taco_gatt_write_transform import (
    PROVIDE_PASSWORD,
    FORCE_ZONE_ON,
    WriteRequest,
)
from .src.callable_entity import (
    CallableSwitch,
    CallableDescription,
    SWITCH_TURN_OFF,
    SWITCH_TURN_ON,
    POLLING_UPDATE,
)

from .const import DOMAIN


_LOGGER = logging.getLogger(__name__)


def _value_fn(data: dict[str, any], index: int, taco_runtime_data: TacoRuntimeData):
    """Returns the zone value at index, 1 based."""

    # Read from internal state for remaining lifetime of entity
    internal_state = taco_runtime_data.force_zone_on[index - 1]
    if internal_state is not None:
        return internal_state

    # Read from the device on initial bootup
    value = data.get(NETWORK_DIAGNOSTIC_FORCE_ZONE_STATUS, None)
    if value is None:
        return None

    external_state = getattr(value, f"zone{index}")
    taco_runtime_data.force_zone_on[index - 1] = external_state
    return external_state


def _write_fn(
    switch_activity: str,
    data: dict[str, any],
    index: int,
    taco_runtime_data: TacoRuntimeData,
) -> list[WriteRequest]:
    """Setup the three actions necessary to actuate a switch"""

    # Because of unreliability with reading the force zone status,
    # and we want home assistant to be the authority,
    # we are relying on the runtime_data internal state rather than
    # anything else to maintain the source of truth for the switch.

    if switch_activity == SWITCH_TURN_ON:
        taco_runtime_data.force_zone_on[index - 1] = True
    elif switch_activity == SWITCH_TURN_OFF:
        taco_runtime_data.force_zone_on[index - 1] = False
    elif switch_activity == POLLING_UPDATE:
        # Make sure the pump status matches the switch status.
        switch_status = taco_runtime_data.force_zone_on[index - 1]
        if switch_status is None:
            return

        zone_info = data.get(ZONE_STATUS, None)
        if zone_info is None:
            return

        if switch_status == getattr(zone_info, f"zone{index}"):
            return

        # Else it looks like for whatever reason the switch
        # doesn't match the zone, so send out another update.
    else:
        _LOGGER.info("Got an unknown switch activity: %s", switch_activity)
        return

    zone_info = ZoneInfo(
        zone1=taco_runtime_data.force_zone_on[0],
        zone2=taco_runtime_data.force_zone_on[1],
        zone3=taco_runtime_data.force_zone_on[2],
        zone4=taco_runtime_data.force_zone_on[3],
        zone5=taco_runtime_data.force_zone_on[4],
        zone6=taco_runtime_data.force_zone_on[5],
    )

    return [
        WriteRequest(PROVIDE_PASSWORD, taco_runtime_data.password),
        WriteRequest(FORCE_ZONE_ON, zone_info),
    ]


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
            hass,
            update_coordinator,
            description,
            name=description.entity_description.key,
            unique_id=create_entity_id(entry, description),
            device_info=create_device_info(DOMAIN, entry),
        )
        for description in switches
        if description.exists_fn(data)
    )
