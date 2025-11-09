"""Actual sensors."""

import logging

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.core import callback

from homeassistant.components.sensor import (
    SensorEntity,
)
from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
)

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from homeassistant.helpers.typing import StateType
from homeassistant.helpers.entity import EntityDescription


_LOGGER = logging.getLogger(__name__)


@dataclass(kw_only=True)
class CallableSensorDescription:
    """Values for use with an EntityDescription"""

    entity_description: EntityDescription
    exists_fn: Callable[[dict[str, any]], bool]
    value_fn: Callable[[dict[str, any]], StateType]


class _BaseCallableSensor(CoordinatorEntity):
    """Representation of a Sensor."""

    entity_description: EntityDescription
    value_fn: Callable[[dict[str, any]], StateType]

    def __init__(
        self,
        update_coordinator: DataUpdateCoordinator,
        sensor_description: CallableSensorDescription,
        name: str,
        unique_id: str,
        device_info: DeviceInfo,
    ) -> None:
        """Set up the instance."""
        super().__init__(update_coordinator)

        self.entity_description = sensor_description.entity_description
        self.value_fn = sensor_description.value_fn

        self._attr_name = name
        self._attr_unique_id = unique_id
        self._attr_device_info = device_info
        self._attr_native_value = None

    @callback
    def _handle_coordinator_update(self) -> None:
        # Not sure I really like this. The availability is determened
        # by the coordinator rather than the sensor or ble device because
        # we are using the CoordinatorEntity. Might rework this...

        _LOGGER.warning("Handle coordinator update...")

        if not self.coordinator.data:
            _LOGGER.warning("No data received from coordinator")
            return

        try:
            self._attr_native_value = self.value_fn(self.coordinator.data)
        except:
            _LOGGER.exception(
                "Failed to update sensor %s with data %s",
                self.name,
                self.coordinator.data,
            )
            raise

        self.async_write_ha_state()


class CallableBinarySensor(_BaseCallableSensor, BinarySensorEntity):
    """Binary Sensor implementation"""

    @property
    def is_on(self) -> bool | None:
        """Return True if the sensor is on."""

        if self._attr_native_value:
            return True
        if self._attr_native_value is False:
            return False
        return None


class CallableSensor(_BaseCallableSensor, SensorEntity):
    """Sensor implementation."""

    # Might need to do a similar property, dunno.
