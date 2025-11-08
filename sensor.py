"""Platform for sensor integration."""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.helpers.device_registry import DeviceInfo

from homeassistant.helpers import device_registry

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    EntityCategory,
    UnitOfElectricCurrent,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import (
    AddConfigEntryEntitiesCallback,
)
from homeassistant.helpers.typing import  StateType

from .const import DOMAIN
from .src.device import TacoDevice
from .src.entry import TacoConfigEntry

_LOGGER = logging.getLogger(__name__)

@dataclass(kw_only=True)
class ExampleSensorEntityDescription(SensorEntityDescription):
    """Describes Example sensor entity."""

    exists_fn: Callable[[TacoDevice], bool] = lambda _: True
    value_fn: Callable[[TacoDevice], StateType]

SENSORS: tuple[ExampleSensorEntityDescription, ...] = (
    ExampleSensorEntityDescription(
        key="estimated_current",
        native_unit_of_measurement=UnitOfElectricCurrent.MILLIAMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda device: 13,
        exists_fn=lambda device: bool(True),
    ),
)

class ExampleSensor(SensorEntity):
    """Representation of a Sensor."""

    entity_description: ExampleSensorEntityDescription
    _attr_entity_category = (
        EntityCategory.DIAGNOSTIC
    )  # This will be common to all instances of ExampleSensorEntity

    def __init__(
        self, device: TacoDevice, entity_description: ExampleSensorEntityDescription
    ) -> None:
        """Set up the instance."""
        self._device = device
        self.entity_description = entity_description
        self._attr_available = False  # This overrides the default
        self._attr_unique_id = f"{device.name}_{entity_description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self.unique_id)},
            name=self.name,
            connections={(device_registry.CONNECTION_BLUETOOTH, device.address)},
        )

    def update(self) -> None:
        """Update entity state."""
        try:
            _LOGGER.debug('Running an update')
            #self._device.update()
        except Exception:
            if self.available:  # Read current state, no need to prefix with _attr_
                _LOGGER.warning("Update failed for %s", self.entity_id)
            self._attr_available = False  # Set property value
            return

        self._attr_available = True
        # We don't need to check if device available here
        self._attr_native_value = self.entity_description.value_fn(
            self._device
        )  # Update "native_value" property


async def async_setup_entry(
    hass: HomeAssistant,
    entry: TacoConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up sensor based on a config entry."""
    _LOGGER.debug("Setting up a sensor: %s", entry)

    taco_config_entry = entry.runtime_data
    taco_device = taco_config_entry.taco_device

    async_add_entities(
        ExampleSensor(taco_device, description)
        for description in SENSORS
        if description.exists_fn(taco_device)
    )
