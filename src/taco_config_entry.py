"""Entry and runtime information for Taco Pump and Zone Controller."""

from dataclasses import dataclass, field

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

    # Not sure how I feel about this. We should really be grabbing the
    # status from the sensors themselves. And also probably wrapping this
    # in an asyncio lock. But thats a lot of extra complexity...
    force_zone_on: list[bool] = field(default_factory=lambda: [False] * 6)


type TacoConfigEntry = ConfigEntry[TacoRuntimeData]
