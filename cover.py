"""Support for EnOcean cover."""
from __future__ import annotations
from email.policy import default

from typing import Any

from enocean.utils import combine_hex
import voluptuous as vol

from homeassistant.components.cover import (
    CoverDeviceClass,
    CoverEntity,
    PLATFORM_SCHEMA,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ID, CONF_NAME, Platform
from homeassistant.const import STATE_CLOSED, STATE_OPEN, STATE_OPENING, STATE_CLOSING
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv, entity_registry as er
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from .const import DOMAIN, LOGGER
from .device import EnOceanEntity

COVER_TYPE_TO_DEVICE_CLASS = {
    "awning": CoverDeviceClass.AWNING,
    "blind": CoverDeviceClass.BLIND,
    "curtain": CoverDeviceClass.CURTAIN,
    "damper": CoverDeviceClass.DAMPER,
    "door": CoverDeviceClass.DOOR,
    "garage": CoverDeviceClass.GARAGE,
    "gate": CoverDeviceClass.GATE,
    "shade": CoverDeviceClass.SHADE,
    "shutter": CoverDeviceClass.SHUTTER,
    "window": CoverDeviceClass.WINDOW,
}

CONF_SENDER_ID = "sender_id"
CONF_REVERSED = False
CONF_DEVICE_CLASS = None
DEFAULT_NAME = "EnOcean Cover"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_ID, default=[]): vol.All(cv.ensure_list, [vol.Coerce(int)]),
        vol.Required(CONF_SENDER_ID): vol.All(cv.ensure_list, [vol.Coerce(int)]),
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Optional(CONF_REVERSED, default=False): cv.bool,
        vol.Optional(
            CONF_DEVICE_CLASS, default=CONF_DEVICE_CLASS
        ): COVER_TYPE_TO_DEVICE_CLASS.get(cv.string, None),
    }
)


def setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the EnOcean cover platform."""
    sender_id = config.get(CONF_SENDER_ID)
    dev_name = config.get(CONF_NAME)
    dev_id = config.get(CONF_ID)
    dev_class = config.get(CONF_DEVICE_CLASS)
    dev_reversed = config.get(CONF_REVERSED)

    add_entities([EnOceanCover(sender_id, dev_id, dev_name, dev_reversed, dev_class)])


class EnOceanCover(EnOceanEntity, CoverEntity):
    """Representation of an EnOcean cover."""

    def __init__(
        self,
        sender_id,
        dev_id,
        dev_name,
        reverse=False,
        device_class=None,
    ):
        """Initialize the cover."""
        super().__init__(dev_id, dev_name)
        self._sender_id = sender_id
        self._attr_unique_id = f"{combine_hex(dev_id)}"
        self._attr_is_closed = None
        self._attr_device_class = device_class
        self._reverse = reverse

    @property
    def name(self):
        """Return the device name."""
        return self.dev_name

    @property
    def is_closed(self):
        """Return whether the cover is closed, open or in between."""
        return self._attr_is_closed

    @property
    def is_closing(self):
        """Return whether the cover is closing or not."""
        return self._attr_is_closing

    @property
    def is_opening(self):
        """Return whether the cover is opening or not."""
        return self._attr_is_opening

    @property
    def current_cover_position(self):
        """Return the position of the cover."""
        return self._attr_current_cover_position

    def press_up_button(self) -> None:
        """Helper Methode to send button up pressed command"""
        data = [0xF6, 0x70]
        data.extend(self._sender_id)
        data.extend([0x30])
        optional = [0x03]
        optional.extend(self.dev_id)
        optional.extend([0x40])  # unknown
        self.send_command(data, optional, 0x01)

    def press_down_button(self) -> None:
        """Helper Methode to send button down pressed command"""
        data = [0xF6, 0x50]
        data.extend(self._sender_id)
        data.extend([0x30])
        optional = [0x03]
        optional.extend(self.dev_id)
        optional.extend([0x40])  # unknown
        self.send_command(data, optional, 0x01)

    def release_button(self) -> None:
        """Helper Methode to send release button command"""
        data = [0xF6, 0x00]
        data.extend(self._sender_id)
        data.extend([0x20])
        optional = [0x03]
        optional.extend(self.dev_id)
        optional.extend([0x40])  # unknown
        self.send_command(data, optional, 0x01)

    def open_cover(self, **kwargs) -> None:
        """Open the cover."""
        self._attr_is_opening = True
        self.schedule_update_ha_state()
        if self._reverse:
            self.press_down_button()
        else:
            self.press_up_button()
        self.release_button()

    def close_cover(self, **kwargs) -> None:
        """Close cover."""
        self._attr_is_closing = True
        self.schedule_update_ha_state()
        if self._reverse:
            self.press_up_button()
        else:
            self.press_down_button()
        self.release_button()

    def stop_cover(self, **kwargs) -> None:
        """Stop the cover."""
        self._attr_is_closing = None
        self._attr_is_opening = None
        self.schedule_update_ha_state()
        self.press_down_button()
        self.release_button()

    def open_cover_tilt(self, **kwargs) -> None:
        """Open the cover tilt."""
        self._attr_is_opening = True
        self.schedule_update_ha_state()
        if self._reverse:
            self.press_down_button()
        else:
            self.press_up_button()
        self.release_button()
        if self._reverse:
            self.press_down_button()
        else:
            self.press_up_button()
        self.release_button()

    def close_cover_tilt(self, **kwargs) -> None:
        """Close the cover tilt."""
        self._attr_is_closing = True
        self.schedule_update_ha_state()
        if self._reverse:
            self.press_up_button()
        else:
            self.press_down_button()
        self.release_button()
        if self._reverse:
            self.press_up_button()
        else:
            self.press_down_button()
        self.release_button()

    def stop_cover_tilt(self, **kwargs) -> None:
        """Stop the cover."""
        self._attr_is_closing = None
        self._attr_is_opening = None
        self.schedule_update_ha_state()
        self.press_down_button()
        self.release_button()

    def value_changed(self, packet):
        """Update the internal state of this device.

        Shutter devices like Becker R30-17-N01 send telegrams with position data.
        We only care about the VLD (0xD2).
        """
        if packet.data[0] == 0xD2 and packet.data[5:8] == self.dev_id:
            val = packet.data[1]
            if val == 0x7F:
                # shutter is moving
                self._attr_is_closed = None
                self.schedule_update_ha_state()
                return

            # shutter has stopped
            self._attr_is_closing = None
            self._attr_is_opening = None

            if val == 0x00:
                # shutter is open
                self._attr_current_cover_position = 0
                self._attr_is_closed = False
                self.schedule_update_ha_state()
                return

            if val == 0x64:
                # shutter is closed
                self._attr_current_cover_position = 100
                self._attr_is_closed = True
                self.schedule_update_ha_state()
                return

            self._attr_current_cover_position = val
            self.schedule_update_ha_state()
