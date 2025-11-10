"""Entities (sensors, switches, etc) that have callbacks."""

import logging

from collections.abc import Callable, Awaitable
from dataclasses import dataclass

from typing import Callable, TypeAlias, Protocol

from homeassistant.core import callback

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

Action: TypeAlias = tuple[str, any]
Data: TypeAlias = dict[str, any]
Exists: TypeAlias = Callable[[Data], bool]
ReadValue: TypeAlias = Callable[[Data], StateType]
WriteValue: TypeAlias = Callable[[str, any], list[Action]]


@dataclass
class CallableDescription:
    """Values for use with an EntityDescription."""

    entity_description: EntityDescription
    exists_fn: Exists
    value_fn: ReadValue | None = None
    write_fn: WriteValue | None = None


class TwoWayDataUpdateCoordinator(DataUpdateCoordinator):
    """A coordinator that can not only read, but also write!."""

    # Ideally this would be a Protocol, but since python doesn't
    # yet have intersection types, well, here we are...

    async def write(self, actions: list[Action]) -> None:
        """The data to write to the coordinator."""
        raise NotImplementedError("Write method not implemented.")


class CallableTwoWayDataUpdateCoordinator(TwoWayDataUpdateCoordinator):
    """A coordinator that can not only read, but also write!."""

    def __init__(
        self,
        hass: HomeAssistant,
        logger: logging.Logger,
        *,
        write_method: Callable[[], Awaitable[None]] | None = None,
        **kwargs,
    ):
        super().__init__(hass, logger, **kwargs)
        self._write_method = write_method

    async def write(self, actions: list[Action]) -> None:
        """The data to write to the coordinator."""

        if self._write_method is None:
            raise NotImplementedError("Write method callback not implemented")

        await self._write_method(actions)


class _BaseCallableCoordinatorEntity(CoordinatorEntity):
    """Representation of a Coordinator Entity."""

    entity_description: EntityDescription
    value_fn: ReadValue | None
    write_fn: WriteValue | None

    def __init__(
        self,
        update_coordinator: TwoWayDataUpdateCoordinator | DataUpdateCoordinator,
        callable_description: CallableDescription,
        name: str,
        unique_id: str,
        device_info: DeviceInfo,
    ) -> None:
        """Set up the instance."""
        super().__init__(update_coordinator)
        self._update_coordinator = update_coordinator

        if not update_coordinator.always_update:
            raise ValueError(
                "Data Update Coordinator must have always update set to True."
            )

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

        if not self._update_coordinator.data:
            _LOGGER.warning(
                "No data received from coordinator for entity %s", self.name
            )
            return

        try:
            previous_value = getattr(self, "_attr_native_value", None)
            next_value = self.value_fn(self._update_coordinator.data)
            if previous_value == next_value:
                return
            _LOGGER.debug("Setting entity %s to %s", self.name, next_value)
            self._attr_native_value = next_value
        except:
            self._attr_native_value = None
            _LOGGER.exception(
                "Failed to update entity %s with data %s",
                self.name,
                self._update_coordinator.data,
            )
            raise

        self.async_write_ha_state()

    async def _handle_coordinator_write(self, actions: list[Action]) -> None:
        """Push data from the entity to the coordinator."""

        # Be careful logging actions, sometimes it includes passwords.
        _LOGGER.debug("Handle coordinator write for entity %s", self.name)

        if not actions:
            _LOGGER.info("No actions to write for entity %s", self.name)
            return

        if not hasattr(self._update_coordinator, "write"):
            # This means you most likely used a DateUpdateCoordinator
            # instead of a TwoWayDataUpdateCoordinator. DataUpdateCoordinators can
            # only be used for read operations. Writes require a TwoWayDataUpdateCoordinator.
            raise ValueError(f"No function to write data with for entity {self.name}")

        try:
            await self._update_coordinator.write(actions)
        except:
            _LOGGER.exception(
                "Failed to write data for entity %s with values %s", self.name, actions
            )
            raise


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

    async def async_turn_on(self) -> None:
        """Turn the entity on."""
        assert self.write_fn

        actions = self.write_fn(SWITCH_TURN_ON)
        await self._handle_coordinator_write(actions)

    async def async_turn_off(self) -> None:
        """Turn the entity off."""
        assert self.write_fn

        actions = self.write_fn(SWITCH_TURN_OFF)
        await self._handle_coordinator_write(actions)
