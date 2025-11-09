"""Entry information for Taco Pump Controller."""

from dataclasses import dataclass

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.config_entries import ConfigEntry

from .ble_data_update_coordinator import BleDataUpdateCoordinator


@dataclass
class TacoRuntimeData:
    """Holds everything our entries need for runtime."""

    address: str
    password: str | None

    update_coordinator: DataUpdateCoordinator
    data_coordinator: BleDataUpdateCoordinator


type TacoConfigEntry = ConfigEntry[TacoRuntimeData]
