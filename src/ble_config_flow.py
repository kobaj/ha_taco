"""Config Flow for the Home Assistant Taco integration."""

from __future__ import annotations

import logging
from typing import Any

from dataclasses import dataclass

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.components.bluetooth import (
    BluetoothServiceInfoBleak,
    async_discovered_service_info,
)
from homeassistant.config_entries import (
    SOURCE_REAUTH,
    SOURCE_RECONFIGURE,
    ConfigFlowResult,
)

from homeassistant.helpers.selector import (
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .ble_service_info_decrypter import BleServiceInfoDecrypter


_LOGGER = logging.getLogger(__name__)

BLE_CONF_DEVICE_NAME = "ble_config_device_name"
BLE_CONF_DEVICE_ADDRESS = "ble_config_device_address"


@dataclass
class AdditionalInfo:
    """Simple extra info to pass along with the device back to entity setup."""

    text_selector_key: str
    text_selector_type: TextSelectorType = TextSelectorType.TEXT
    is_required: bool = True


class BleConfigFlow(config_entries.ConfigFlow):
    """Generic config flow for bluetooth device."""

    # The schema version of the entries that it creates
    # Home Assistant will call your migrate method if the version changes
    VERSION = 1
    MINOR_VERSION = 1

    def __init__(
        self, decrypter: BleServiceInfoDecrypter, additional_info: list[AdditionalInfo]
    ) -> None:
        """Initialize the config flow."""
        self._discovery_info: BluetoothServiceInfoBleak | None = None
        self._discovery_infos: list[BluetoothServiceInfoBleak] = []
        self._decrypter = decrypter
        self._additional_info = additional_info

    async def async_step_bluetooth(
        self, discovery_info: BluetoothServiceInfoBleak
    ) -> ConfigFlowResult:
        """Initial entry point for the Bluetooth discovery step."""
        _LOGGER.debug("Starting bluetooth: %s", discovery_info.address)

        if not self._decrypter.is_valid_device(discovery_info):
            return self.async_abort(reason="not_supported")

        current_addresses = self._async_current_ids()
        if discovery_info.address in current_addresses:
            return self.async_abort(reason="already_configured")

        self._discovery_info = discovery_info
        return self.show_confirm()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Initial entry point for a user clicking on our integration."""
        _LOGGER.debug("Starting user device selection: %s", user_input)

        current_addresses = self._async_current_ids()
        self._discovery_infos = []
        for discovery_info in async_discovered_service_info(self.hass, False):
            address = discovery_info.address
            if address in current_addresses:
                continue
            if not self._decrypter.is_valid_device(discovery_info):
                continue
            self._discovery_infos.append(discovery_info)

        if not self._discovery_infos:
            return self.async_abort(reason="no_devices_found")
        return self.show_device_selection()

    def show_device_selection(self) -> ConfigFlowResult:
        """Show the device selection dialog."""

        assert self._discovery_infos

        address_by_name = dict(
            (di.address, self._decrypter.get_device_name(di))
            for di in self._discovery_infos
        )
        title = "device_selection"
        placeholders = {"name": title}
        self.context["title_placeholders"] = placeholders
        return self.async_show_form(
            step_id="device_selection",
            description_placeholders=placeholders,
            data_schema=vol.Schema(
                {vol.Required(BLE_CONF_DEVICE_ADDRESS): vol.In(address_by_name)}
            ),
        )

    async def async_step_device_selection(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        "Process the user's device selection."
        _LOGGER.debug("Got user device selection: %s", user_input)

        if user_input is None:
            return self.show_device_selection()
        assert self._discovery_infos

        address = user_input[BLE_CONF_DEVICE_ADDRESS]
        self._discovery_info = next(
            di for di in self._discovery_infos if di.address == address
        )
        return self.show_confirm()

    def show_confirm(self) -> ConfigFlowResult:
        """Show the configuration dialog."""

        assert self._discovery_info

        title = self._decrypter.get_device_name(self._discovery_info)
        address = self._discovery_info.device.address
        placeholders = {"name": title}
        self.context["title_placeholders"] = placeholders
        return self.async_show_form(
            step_id="confirm",
            description_placeholders=placeholders,
            data_schema=vol.Schema(
                {
                    vol.Required(BLE_CONF_DEVICE_NAME, default=title): TextSelector(
                        TextSelectorConfig(read_only=True)
                    ),
                    vol.Required(
                        BLE_CONF_DEVICE_ADDRESS, default=address
                    ): TextSelector(TextSelectorConfig(read_only=True)),
                    **{
                        vol.Required(ai.text_selector_key): TextSelector(
                            TextSelectorConfig(type=ai.text_selector_type)
                        )
                        for ai in self._additional_info
                        if ai.is_required
                    },
                    **{
                        vol.Optional(ai.text_selector_key): TextSelector(
                            TextSelectorConfig(type=ai.text_selector_type)
                        )
                        for ai in self._additional_info
                        if not ai.is_required
                    },
                }
            ),
        )

    async def async_step_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Process the user's final input configuration values."""
        _LOGGER.debug("Got user configuration: %s", user_input)

        if user_input is None:
            # I would expect us to abort here, but apparently this infinite loop is
            # not only recommended, but required. WTF home assistant...
            return self.show_confirm()
        assert self._discovery_info

        address = self._discovery_info.address
        await self.async_set_unique_id(address)
        if self.source == SOURCE_REAUTH:
            self._abort_if_unique_id_mismatch()
            return self.async_update_reload_and_abort(
                self._get_reauth_entry(),
                data_updates=user_input,
            )
        if self.source == SOURCE_RECONFIGURE:
            self._abort_if_unique_id_mismatch()
            return self.async_update_reload_and_abort(
                self._get_reconfigure_entry(),
                data_updates=user_input,
            )
        self._abort_if_unique_id_configured()

        title = self._decrypter.get_device_name(self._discovery_info)
        return self.async_create_entry(title=title, data=user_input)

    async def async_step_reauth(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Perform reauth upon an API authentication error."""

        address = self._get_reauth_entry().runtime_data.address
        self._discovery_info = next(
            di
            for di in async_discovered_service_info(self.hass, False)
            if di.address == address
        )

        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Dialog that informs the user that reauth is required."""
        if user_input is None:
            return self.async_show_form(
                step_id="reauth_confirm",
                data_schema=vol.Schema({}),
            )
        return await self.async_step_confirm()

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Step that lets a user reconfigure their device."""

        address = self._get_reconfigure_entry().runtime_data.address
        self._discovery_info = next(
            di
            for di in async_discovered_service_info(self.hass, False)
            if di.address == address
        )

        return await self.async_step_confirm()
