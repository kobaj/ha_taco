from homeassistant.helpers.device_registry import DeviceInfo

from homeassistant.helpers import device_registry

from .callable_sensor import CallableSensorDescription
from .taco_config_entry import TacoConfigEntry


def create_sensor_id(
    entry: TacoConfigEntry, sensor_description: CallableSensorDescription
) -> str:
    """Create a unique id for a sensor."""
    return f"{entry.unique_id}_{sensor_description.entity_description.key}"


def create_device_info(domain: str, entry: TacoConfigEntry) -> DeviceInfo:
    """Create DeviceInfo for sensors."""

    taco_runtime_data = entry.runtime_data
    return DeviceInfo(
        identifiers={(domain, entry.unique_id)},
        manufacturer="Taco",
        connections={(device_registry.CONNECTION_BLUETOOTH, taco_runtime_data.address)},
    )
