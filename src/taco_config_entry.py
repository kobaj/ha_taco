"""Entry and runtime information for Taco Pump and Zone Controller."""

from dataclasses import dataclass, field, InitVar
from typing import Callable

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .taco_gatt_write_transform import MaskedString
from .ble_data_update_coordinator import BleDataUpdateCoordinator

@dataclass
class TacoRuntimeData:
    """Holds everything our entries need for runtime."""

    address: str

    update_coordinator: DataUpdateCoordinator
    ble_coordinator: BleDataUpdateCoordinator

    password: InitVar[str | None] = None
    _masked_password: MaskedString | None = None

    remove_listeners: Callable[[], None] = lambda: None
    force_zone_on: list[bool] = field(default_factory=lambda: [False] * 6)

    def __post_init__(self, password: str | None):
        self.password = password

    @property
    def password(self) -> MaskedString | None:  # noqa: F811
        return self._masked_password

    @password.setter
    def password(self, password: str | None) -> None:
        if not password:
            self._masked_password = None
            return

        self._masked_password = MaskedString(password)


type TacoConfigEntry = ConfigEntry[TacoRuntimeData]
