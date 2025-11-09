"""Config Flow for Taco bluetooth devices."""

import logging

from homeassistant.helpers.selector import (
    TextSelectorType,
)

from .src.ble_config_flow import BleConfigFlow, AdditionalInfo

from .const import DOMAIN, taco_service_info_decrypter


_LOGGER = logging.getLogger(__name__)

CONF_TACO_DEVICE_PASSWORD = "ble_config_device_password"


class TacoConfigFlow(BleConfigFlow, domain=DOMAIN):
    """The actual config flow used to setup Taco devices in home assistant."""

    def __init__(self):
        super().__init__(
            decrypter=taco_service_info_decrypter,
            additional_info=[
                AdditionalInfo(
                    text_selector_key=CONF_TACO_DEVICE_PASSWORD,
                    text_selector_type=TextSelectorType.PASSWORD,
                    is_required=False,
                )
            ],
        )
