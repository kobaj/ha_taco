"""Methods used inside of __init__.py for setting up the taco."""

from datetime import datetime, timedelta
import logging

from homeassistant.helpers.event import async_track_time_interval
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.core import HomeAssistant

from .taco_gatt_write_transform import (
    PROVIDE_PASSWORD,
    REQUEST_FORCE_ZONE_STATUS,
    WriteRequest,
    FORCE_ZONE_ON,
)
from .taco_config_entry import TacoRuntimeData
from .taco_gatt_read_transform import ZoneInfo
from .ble_data_update_coordinator import BleDataUpdateCoordinator


_LOGGER = logging.getLogger(__name__)


async def _validate_password(password, ble_coordinator: BleDataUpdateCoordinator):
    """Checks the password is legal and actually correct for this particular device."""

    if password and len(password) > 20:
        raise ConfigEntryAuthFailed(
            "Cannot have a Taco password more than 20 characters."
        )

    if password:
        try:
            await ble_coordinator.write([WriteRequest(PROVIDE_PASSWORD, password)])
        except Exception as err:
            raise ConfigEntryAuthFailed(err) from err


async def send_initial_write_requests(runtime_data: TacoRuntimeData):
    """Starts communication with the taco, validating passwords and connections."""

    await _validate_password(runtime_data.password, runtime_data.ble_coordinator)

    # TODO Note we can only make a single write request at the moment.
    # Because you must wait some time to read the result. Only after
    # getting a successful read can you then make another write request.
    #
    # See comment inside of taco_gatt_Write_transform.py
    await runtime_data.ble_coordinator.write(
        [
            WriteRequest(PROVIDE_PASSWORD, runtime_data.password),
            WriteRequest(REQUEST_FORCE_ZONE_STATUS),
        ]
    )


def _create_write_requests(runtime_data: TacoRuntimeData) -> list[WriteRequest]:
    """The write action that should take place upon a successful loop."""

    if runtime_data.force_zone_on[0] == None:
        # Don't need to check all 6 force zone on, none are yet initialized.
        return []

    zone_info = ZoneInfo(
        zone1=runtime_data.force_zone_on[0],
        zone2=runtime_data.force_zone_on[1],
        zone3=runtime_data.force_zone_on[2],
        zone4=runtime_data.force_zone_on[3],
        zone5=runtime_data.force_zone_on[4],
        zone6=runtime_data.force_zone_on[5],
    )

    return [
        WriteRequest(PROVIDE_PASSWORD, runtime_data.password),
        WriteRequest(FORCE_ZONE_ON, zone_info),
    ]


async def _send_write_requests(
    actions: list[WriteRequest], ble_coordinator: BleDataUpdateCoordinator
) -> bool:
    _LOGGER.debug(
        "Sending out write requests (%s): %s",
        len(actions),
        [a for a in actions if a.action != PROVIDE_PASSWORD],
    )
    await ble_coordinator.write(actions)


_PREVIOUS_ACTIONS_KEY = "previous_actions"
_PREVIOUS_WRITE_TIME_KEY = "previous_write_time"


async def _loop(state: dict, runtime_data: TacoRuntimeData):
    """The actual loop called every few seconds."""

    # The Taco is pretty defensive and will timeout after
    # 5 minutes. So we need to repeatedly send it the same commands
    # over and over again to keep it awake and acting like we want.

    success = False

    actions = _create_write_requests(runtime_data)

    if not actions:
        return

    previous_actions = state.get(_PREVIOUS_ACTIONS_KEY, [])
    if previous_actions != actions:
        await _send_write_requests(actions, runtime_data.ble_coordinator)
        success = True

    # The Taco times out after 5 minutes, so set this to be just a bit before.
    previous_datetime = state.get(_PREVIOUS_WRITE_TIME_KEY, datetime.now())
    if datetime.now() - previous_datetime > timedelta(minutes=4):
        await _send_write_requests(actions, runtime_data.ble_coordinator)
        success = True

    if success:
        state[_PREVIOUS_ACTIONS_KEY] = actions
        state[_PREVIOUS_WRITE_TIME_KEY] = datetime.now()


async def setup_write_loop(hass: HomeAssistant, runtime_data: TacoRuntimeData):
    """Sets up the loop(s) that write data back to the device."""

    state = {}

    async def _stateless_loop(_time):
        await _loop(state, runtime_data)

    return async_track_time_interval(
        hass,
        _stateless_loop,
        # Don't change this, we need it to be relatively fast
        # If you want to adjust things, adjust inside of _loop.
        timedelta(seconds=1),
    )
