## About

Home Assistant Integration that allows you to manage a Taco pump and zone controller via its bluetooth interface.

Specifically this will allow you to see the status of your pumps, and the thermostats feeding them (eg, on or off). If you have the password to your Taco device (found on the inside of the green cover, printed on the circuit board) you can also override the pumps.

Follow both the Installation and Setup instructions below.

Confirmed working with the following, however it should work with any bluetooth enabled Taco pump and zone controller.

|Model|HardwareRevision|Firmware|
|--|--|--|
|SR503|1|<todo>|

## Installation

### HACS method (recommended)

This is based on the instructions at

1. Navigate to the HACS ui inside your home assistant instance.
1. Click on the 3 dots in the top right corner.
1. Select "Custom repositories"
1. Add the URL `https://gitlab.com/kobaj/ha_taco.git` to the repository.
1. Select `Integration` as the type.
1. Click the "ADD" button.

### Manual method (not recommended)

1. On your Home Assistant box, cd into your `config/custom_components` directory
1. Run `git clone git@gitlab.com:kobaj/ha_taco.git`

## Setup

1. Navigate to your `Devices & services` inside of Home Assistant `Settings`
1. Click `Add New Integration` and search for `Taco`

<todo> explain the password and show a screenshot of the setup steps

## Debugging

To show log messages from this particular custom component then put the following in your configuration.yaml

```
logger:
  default: warning
  logs:
    custom_components.ha_taco: debug
```
