from homeassistant.helpers.device_registry import DeviceInfo

from homeassistant.helpers import device_registry

from .callable_entity import CallableDescription
from .taco_config_entry import TacoConfigEntry


def create_entity_id(
    entry: TacoConfigEntry, callable_description: CallableDescription
) -> str:
    """Create a unique id for a sensor."""
    return f"{entry.unique_id}_{callable_description.entity_description.key}"


def create_device_info(domain: str, entry: TacoConfigEntry) -> DeviceInfo:
    """Create DeviceInfo for sensors."""

    taco_runtime_data = entry.runtime_data
    return DeviceInfo(
        identifiers={(domain, entry.unique_id)},
        manufacturer="Taco",
        connections={(device_registry.CONNECTION_BLUETOOTH, taco_runtime_data.address)},
    )
