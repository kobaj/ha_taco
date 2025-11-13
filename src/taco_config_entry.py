"""Entry and runtime information for Taco Pump and Zone Controller."""

from dataclasses import dataclass, field
from typing import Callable

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .ble_data_update_coordinator import BleDataUpdateCoordinator


@dataclass
class TacoRuntimeData:
    """Holds everything our entries need for runtime."""

    address: str

    update_coordinator: DataUpdateCoordinator
    ble_coordinator: BleDataUpdateCoordinator

    password: str | None = None

    remove_listeners: Callable[[], None] = lambda: None
    force_zone_on: list[bool] = field(default_factory=lambda: [None] * 6)


type TacoConfigEntry = ConfigEntry[TacoRuntimeData]
