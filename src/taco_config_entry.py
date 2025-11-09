"""Entry information for Taco Pump Controller."""

from dataclasses import dataclass

from homeassistant.config_entries import ConfigEntry

from .ble_data_update_coordinator import BleDataUpdateCoordinator
from .callable_entity import TwoWayDataUpdateCoordinator


@dataclass
class TacoRuntimeData:
    """Holds everything our entries need for runtime."""

    address: str
    password: str | None

    update_coordinator: TwoWayDataUpdateCoordinator
    _data_coordinator: BleDataUpdateCoordinator


type TacoConfigEntry = ConfigEntry[TacoRuntimeData]
