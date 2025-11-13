"""Entities (sensors, switches, etc) that have callbacks."""

import logging

from collections.abc import Callable
from dataclasses import dataclass

from typing import Callable, TypeAlias

from homeassistant.core import callback, HomeAssistant

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
)

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.entity import EntityDescription

from homeassistant.components.switch import SwitchEntity


_LOGGER = logging.getLogger(__name__)


Data: TypeAlias = dict[str, any]
Exists: TypeAlias = Callable[[Data], bool]
ReadValue: TypeAlias = Callable[[Data], StateType]
WriteValue: TypeAlias = Callable[[str, Data], None]


@dataclass
class CallableDescription:
    """Values for use with an EntityDescription."""

    entity_description: EntityDescription
    exists_fn: Exists
    value_fn: ReadValue | None = None
    write_fn: WriteValue | None = None


class _BaseCallableCoordinatorEntity(CoordinatorEntity):
    """Representation of a Coordinator Entity."""

    entity_description: EntityDescription
    value_fn: ReadValue | None
    write_fn: WriteValue | None

    def __init__(
        self,
        update_coordinator: DataUpdateCoordinator,
        callable_description: CallableDescription,
        name: str,
        unique_id: str,
        device_info: DeviceInfo,
    ) -> None:
        """Set up the instance."""
        super().__init__(update_coordinator)

        self.entity_description = callable_description.entity_description
        self.value_fn = callable_description.value_fn
        self.write_fn = callable_description.write_fn

        self._attr_name = name
        self._attr_unique_id = unique_id
        self._attr_device_info = device_info
        self._attr_native_value = None

    @callback
    def _handle_coordinator_update(self) -> None:
        """Read data from the coordinator and process it into the entity."""

        # Not sure I really like this. The availability is determened
        # by the coordinator rather than the sensor or ble device because
        # we are using the CoordinatorEntity. Might rework this...

        _LOGGER.debug("Handle coordinator update for entity %s", self.name)

        if not self.value_fn:
            _LOGGER.info("No function to consume data with for entity %s", self.name)
            return

        if not self.coordinator.data:
            _LOGGER.warning(
                "No data received from coordinator for entity %s", self.name
            )
            return

        try:
            previous_value = getattr(self, "_attr_native_value", None)
            next_value = self.value_fn(self.coordinator.data)
            if previous_value == next_value:
                return
            _LOGGER.debug("Setting entity %s to %s", self.name, next_value)
            self._attr_native_value = next_value
        except:
            self._attr_native_value = None
            _LOGGER.exception(
                "Failed to update entity %s with data %s",
                self.name,
                self.coordinator.data,
            )
            raise

        self.async_write_ha_state()


class CallableBinarySensor(_BaseCallableCoordinatorEntity, BinarySensorEntity):
    """Binary Sensor implementation."""

    @property
    def is_on(self) -> bool | None:
        """Return True if the sensor is on."""

        if self._attr_native_value:
            return True
        if self._attr_native_value is False:
            return False
        return None


SWITCH_TURN_ON = "switch_turn_on"
SWITCH_TURN_OFF = "switch_turn_off"


class CallableSwitch(_BaseCallableCoordinatorEntity, SwitchEntity):
    """Switch implementation."""

    @property
    def is_on(self) -> bool | None:
        """Return True if the switch is on."""

        if self._attr_native_value:
            return True
        if self._attr_native_value is False:
            return False
        return None

    async def _async_actuate(self, switch_activity: str):
        """Turn the switch on or off based on the activity"""
        if not self.write_fn:
            raise ValueError(
                f"Need a write_fn passed to CallableEntity for Switch {self.name}."
            )

        self.write_fn(switch_activity, getattr(self.coordinator, "data", {}))

        # Trigger an immediate state read so the UI is reflected very quickly.
        self._handle_coordinator_update()

    async def async_turn_on(self) -> None:
        """Turn the entity on."""
        await self._async_actuate(SWITCH_TURN_ON)

    async def async_turn_off(self) -> None:
        """Turn the entity off."""
        await self._async_actuate(SWITCH_TURN_OFF)
