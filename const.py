"""Constants for the Home Assistant Taco integration."""

from logging import Logger, getLogger


from .src.gatt import Gatt, Service, Characteristic, Property, ReadAction
from .src.ble_service_info_decrypter import BleServiceInfoDecrypter
from .src.taco_gatt_read_transform import (
    read_network_thermostat_input_status_transform,
    read_network_zone_count_transform,
    read_network_zone_status_transform,
    read_product_id_transform,
    read_network_diagnostic_data_transform,
    read_log_transform,
    read_network_aux1_transform,
    read_network_aux2_transform,
)
from .src.taco_gatt_write_transform import (
    write_password_transform,
    write_network_diagnostic_mode_transform,
)

LOGGER: Logger = getLogger(__package__)

DOMAIN = "ha_taco"

_TACO_SERVICES = [
    Service(
        uuid="38f63141-02b6-403c-810c-7e1253f474eb",
        name="Diagnostics",
        characteristics=[
            Characteristic(
                uuid="38f6314b-02b6-403c-810c-7e1253f474eb",
                name="platformId",
                properties=[Property.READ],
            ),
            Characteristic(
                uuid="38f63144-02b6-403c-810c-7e1253f474eb",
                name="firmwareVersion",
                properties=[Property.READ],
            ),
            Characteristic(
                uuid="38f63142-02b6-403c-810c-7e1253f474eb",
                name="productId",
                properties=[Property.READ],
            ),
            Characteristic(
                uuid="38f63143-02b6-403c-810c-7e1253f474eb",
                name="serialNumber",
                properties=[Property.READ],
            ),
            Characteristic(
                uuid="38f63145-02b6-403c-810c-7e1253f474eb",
                name="status",
                properties=[Property.READ, Property.NOTIFY],
            ),
            Characteristic(
                uuid="38f63146-02b6-403c-810c-7e1253f474eb",
                name="deviceName",
                properties=[Property.READ, Property.WRITE],
            ),
            Characteristic(
                uuid="38f63147-02b6-403c-810c-7e1253f474eb",
                name="location",
                properties=[Property.READ, Property.WRITE],
            ),
            Characteristic(
                uuid="38f63148-02b6-403c-810c-7e1253f474eb",
                name="notes",
                properties=[Property.READ, Property.WRITE, Property.EXTENDED_PROPS],
            ),
            # Must be set before any diagnostic and config writes can take place.
            Characteristic(
                uuid="38f63149-02b6-403c-810c-7e1253f474eb",
                name="password",
                properties=[Property.WRITE],
                write_transform=write_password_transform,
            ),
            Characteristic(
                uuid="38f6314a-02b6-403c-810c-7e1253f474eb",
                name="interfaceRevision",
                properties=[Property.READ],
            ),
            Characteristic(
                uuid="38f6314c-02b6-403c-810c-7e1253f474eb",
                name="diagnosticMode",
                properties=[Property.READ, Property.WRITE],
            ),
        ],
    ),
    Service(
        uuid="1b423141-e0eb-4d9e-a86b-dcabcc3565b9",
        name="ZoneControl",
        characteristics=[
            # This is the mac address, it seems like the official app
            # uses this as a kind of ping by reading the value, and then
            # writing back the exact same value it just read.
            Characteristic(
                uuid="1b423159-e0eb-4d9e-a86b-dcabcc3565b9",
                name="networkDeviceIndex",
                properties=[Property.READ, Property.WRITE],
            ),
            Characteristic(
                uuid="1b42315c-e0eb-4d9e-a86b-dcabcc3565b9",
                name="networkDeviceName",
                properties=[Property.READ, Property.WRITE],
            ),
            Characteristic(
                uuid="1b423161-e0eb-4d9e-a86b-dcabcc3565b9",
                name="networkProductId",
                properties=[Property.READ],
                read_action=ReadAction.INDEX,
                read_transform=read_product_id_transform,
            ),
            # How to read diagnostic data (eg, zone overrides).
            Characteristic(
                uuid="1b42315e-e0eb-4d9e-a86b-dcabcc3565b9",
                name="networkDiagnosticData",
                properties=[Property.READ, Property.INDICATE],
                read_action=ReadAction.AFTER_NOTIFICATION,
                read_transform=read_network_diagnostic_data_transform,
            ),
            Characteristic(
                uuid="1b423162-e0eb-4d9e-a86b-dcabcc3565b9",
                name="networkFirmwareVersion",
                properties=[Property.READ],
            ),
            Characteristic(
                uuid="1b423144-e0eb-4d9e-a86b-dcabcc3565b9",
                name="networkDIPInputStatus",
                properties=[Property.READ, Property.NOTIFY],
            ),
            Characteristic(
                uuid="1b423145-e0eb-4d9e-a86b-dcabcc3565b9",
                name="pumpExerciseOffTime",
                properties=[Property.READ, Property.WRITE],
            ),
            Characteristic(
                uuid="1b423146-e0eb-4d9e-a86b-dcabcc3565b9",
                name="pumpExerciseOnTime",
                properties=[Property.READ, Property.WRITE],
            ),
            Characteristic(
                uuid="1b42315a-e0eb-4d9e-a86b-dcabcc3565b9",
                name="postPurgeTime",
                properties=[Property.READ, Property.WRITE],
            ),
            Characteristic(
                uuid="1b423148-e0eb-4d9e-a86b-dcabcc3565b9",
                name="zvcInterfaceRevision",
                properties=[Property.READ],
            ),
            Characteristic(
                uuid="1b423149-e0eb-4d9e-a86b-dcabcc3565b9",
                name="networkZoneNames",
                properties=[Property.READ, Property.WRITE, Property.EXTENDED_PROPS],
            ),
            Characteristic(
                uuid="1b42314b-e0eb-4d9e-a86b-dcabcc3565b9",
                name="networkId",
                properties=[Property.READ],
            ),
            Characteristic(
                uuid="1b423160-e0eb-4d9e-a86b-dcabcc3565b9",
                name="networkDeviceLocation",
                properties=[Property.READ, Property.WRITE],
            ),
            Characteristic(
                uuid="1b42314e-e0eb-4d9e-a86b-dcabcc3565b9",
                name="networkAddressMapping",
                properties=[Property.READ, Property.NOTIFY],
            ),
            Characteristic(
                uuid="1b42314f-e0eb-4d9e-a86b-dcabcc3565b9",
                name="networkAddressStatus",
                properties=[Property.READ, Property.NOTIFY],
            ),
            # Very important, tells us how many buttons we have!
            Characteristic(
                uuid="1b423150-e0eb-4d9e-a86b-dcabcc3565b9",
                name="networkZoneCount",
                properties=[Property.READ],
                read_action=ReadAction.INDEX,
                read_transform=read_network_zone_count_transform,
            ),
            # This is the thermostat status.
            Characteristic(
                uuid="1b423151-e0eb-4d9e-a86b-dcabcc3565b9",
                name="networkThermostatInputStatus",
                properties=[Property.READ, Property.NOTIFY],
                read_action=ReadAction.SUBSCRIBE,
                read_transform=read_network_thermostat_input_status_transform,
            ),
            # This is the pump and zone status.
            Characteristic(
                uuid="1b423152-e0eb-4d9e-a86b-dcabcc3565b9",
                name="networkZoneStatus",
                properties=[Property.READ, Property.NOTIFY],
                read_action=ReadAction.SUBSCRIBE,
                read_transform=read_network_zone_status_transform,
            ),
            Characteristic(
                uuid="1b423153-e0eb-4d9e-a86b-dcabcc3565b9",
                name="networkMainBoilerEndSwitch",
                properties=[Property.READ, Property.WRITE],
            ),
            Characteristic(
                uuid="1b423154-e0eb-4d9e-a86b-dcabcc3565b9",
                name="networkPriorityBoilerEndSwitch",
                properties=[Property.READ, Property.WRITE],
            ),
            # For whatever reason these aux are not reporting
            # their state via bluetooth, so don't include them.
            Characteristic(
                uuid="1b423155-e0eb-4d9e-a86b-dcabcc3565b9",
                name="networkAux1",
                properties=[Property.READ, Property.WRITE],
                # read_action=ReadAction.AFTER_NOTIFICATION,
                # read_transform=read_network_aux1_transform,
            ),
            Characteristic(
                uuid="1b423156-e0eb-4d9e-a86b-dcabcc3565b9",
                name="networkAux2",
                properties=[Property.READ, Property.WRITE],
                # read_action=ReadAction.AFTER_NOTIFICATION,
                # read_transform=read_network_aux2_transform,
            ),
            # That's weird, the Taco documentation doesn't mention
            # that any of their units have a third aux...
            Characteristic(
                uuid="1b423157-e0eb-4d9e-a86b-dcabcc3565b9",
                name="networkAux3",
                properties=[Property.READ, Property.WRITE],
            ),
            Characteristic(
                uuid="1b42315b-e0eb-4d9e-a86b-dcabcc3565b9",
                name="networkOutputNames",
                properties=[Property.READ, Property.WRITE, Property.EXTENDED_PROPS],
            ),
            Characteristic(
                uuid="1b423158-e0eb-4d9e-a86b-dcabcc3565b9",
                name="operatingMode",
                properties=[Property.READ, Property.WRITE],
            ),
            # This is how to trigger a pump or zone manually.
            Characteristic(
                uuid="1b42315d-e0eb-4d9e-a86b-dcabcc3565b9",
                name="networkDiagnosticMode",
                properties=[Property.READ, Property.WRITE],
                write_transform=write_network_diagnostic_mode_transform,
            ),
            Characteristic(
                uuid="1b42315f-e0eb-4d9e-a86b-dcabcc3565b9",
                name="networkRecircMode",
                properties=[Property.READ, Property.WRITE],
            ),
        ],
    ),
]

taco_gatt = Gatt(services=_TACO_SERVICES)

# 3155 is 0x0C53, Taco Inc
taco_service_info_decrypter = BleServiceInfoDecrypter(
    manufacturer_id=3155,
    service_ids=[service.uuid for service in taco_gatt.services],
)
