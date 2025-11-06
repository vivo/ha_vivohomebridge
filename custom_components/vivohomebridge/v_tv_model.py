"""
 Copyright 2024 vivo Mobile Communication Co., Ltd.
 Licensed under the Apache License, Version 2.0 (the "License");

    http://www.apache.org/licenses/LICENSE-2.0
"""
import json
from typing import List, Mapping, Any

from homeassistant.components.media_player import ATTR_MEDIA_VOLUME_LEVEL, MediaPlayerEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    SERVICE_VOLUME_SET, SERVICE_MEDIA_PREVIOUS_TRACK, SERVICE_MEDIA_NEXT_TRACK,
    SERVICE_MEDIA_STOP, Platform, SERVICE_TURN_ON, SERVICE_TURN_OFF
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import (
    device_registry as dr,
    entity_registry as er
)
from .v_attribute import (
    VIVO_ATTR_NAME_POWER, HA_ATTR_NAME_POWER, VIVO_KEY_WORD_V_NAME, VIVO_KEY_WORD_H_NAME, VIVO_ATTR_NAME_HOME,
    HA_ATTR_NAME_HOME, VIVO_ATTR_NAME_MENU, HA_ATTR_NAME_MENU, VIVO_ATTR_NAME_ENTER, HA_ATTR_NAME_ENTER,
    VIVO_ATTR_NAME_BACK, HA_ATTR_NAME_BACK, VIVO_ATTR_NAME_LEFT, HA_ATTR_NAME_LEFT, VIVO_ATTR_NAME_RIGHT,
    HA_ATTR_NAME_RIGHT, VIVO_ATTR_NAME_UP, HA_ATTR_NAME_UP, VIVO_ATTR_NAME_DOWN, HA_ATTR_NAME_DOWN,
    VIVO_ATTR_NAME_VOLUME, HA_ATTR_NAME_VOLUME, VIVO_ATTR_NAME_VOLUME_UP, HA_ATTR_NAME_VOLUME_UP,
    VIVO_ATTR_NAME_VOLUME_DOWN, HA_ATTR_NAME_VOLUME_DOWN, VIVO_ATTR_NAME_MUTE, HA_ATTR_NAME_MUTE, VIVO_ATTR_NAME_PLAY,
    HA_ATTR_NAME_PLAY, VIVO_ATTR_NAME_PAUSE, HA_ATTR_NAME_PAUSE, VIVO_ATTR_NAME_PREVIOUS, HA_ATTR_NAME_PREVIOUS,
    VIVO_ATTR_NAME_NEXT, HA_ATTR_NAME_NEXT, VIVO_ATTR_NAME_STOP, HA_ATTR_NAME_STOP, VIVO_ATTR_VALUE_POWER_OFF,
    VIVO_ATTR_VALUE_POWER_ON, VIVO_ATTR_VALUE_HOME, HA_ATTR_VALUE_HOME, VIVO_ATTR_VALUE_MENU, HA_ATTR_VALUE_MENU,
    VIVO_ATTR_VALUE_ENTER, HA_ATTR_VALUE_ENTER, VIVO_ATTR_VALUE_BACK, HA_ATTR_VALUE_BACK, VIVO_ATTR_VALUE_LEFT,
    HA_ATTR_VALUE_LEFT, VIVO_ATTR_VALUE_RIGHT, HA_ATTR_VALUE_RIGHT, HA_ATTR_VALUE_UP, VIVO_ATTR_VALUE_UP,
    VIVO_ATTR_VALUE_DOWN, HA_ATTR_VALUE_DOWN, VIVO_ATTR_VALUE_VOLUME_UP, HA_LG_ATTR_NAME_VOLUME_UP,
    VIVO_ATTR_VALUE_VOLUME_DOWN, HA_LG_ATTR_NAME_VOLUME_DOWN, VIVO_ATTR_VALUE_MUTE, VIVO_ATTR_VALUE_PLAY,
    VIVO_ATTR_VALUE_PAUSE, VIVO_ATTR_VALUE_PREVIOUS, VIVO_ATTR_VALUE_NEXT, VIVO_ATTR_VALUE_STOP,
    VIVO_ATTR_NAME_REMOTE_POWER, HA_ATTR_NAME_REMOTE_POWER, VIVO_ATTR_NAME_WAKE_UP, HA_ATTR_NAME_WAKE_UP,
    VIVO_ATTR_NAME_TOP_MENU, HA_ATTR_NAME_TOP_MENU, VIVO_ATTR_VALUE_REMOTE_POWER_OFF, VIVO_ATTR_VALUE_REMOTE_POWER_ON,
    VIVO_ATTR_VALUE_WAKE_UP, HA_ATTR_VALUE_WAKE_UP, HA_ATTR_VALUE_STOP, VIVO_ATTR_VALUE_TOP_MENU,
    HA_ATTR_VALUE_TOP_MENU, HA_APPLE_ATTR_VALUE_ENTER, HA_ATTR_VALUE_PLAY, HA_ATTR_VALUE_PAUSE, HA_ATTR_VALUE_VOLUME_UP,
    HA_ATTR_VALUE_VOLUME_DOWN, HA_ATTR_VALUE_PREVIOUS, HA_ATTR_VALUE_NEXT
)
from .v_utils.vattributes_utils import VAttributeUtils
from .v_utils.vlog import VLog

_TAG = "tv"


class VTVModel:
    LG_IDENTIFIER_ID = "webostv"
    APPLE_IDENTIFIER_ID = "apple_tv"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, identify_id_list: List[str]) -> None:
        if identify_id_list is None or len(identify_id_list) == 0:
            return
        for identifyId in identify_id_list:
            if identifyId == self.LG_IDENTIFIER_ID:
                self.vLGTV = VLGTV(hass, entry, identifyId)
            elif identifyId == self.APPLE_IDENTIFIER_ID:
                self.vAppleTV = VAppleTV(hass, entry, identifyId)


class VTVCommon:
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, domain: str) -> None:
        """Initialize the TV instance,as Common mode."""
        self.hass = hass
        self.entry = entry
        self.domain = domain


class VLGTV(VTVCommon):
    BRAND_NAME = "LG"
    _LG_SERVICE_COMMAND = "button"
    _LG_COMMAND_PARAM: dict = {"target_domain": VTVModel.LG_IDENTIFIER_ID}

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, domain: str) -> None:
        super().__init__(hass, entry, domain)
        self.attributes_map = [
            {
                VIVO_KEY_WORD_V_NAME: VIVO_ATTR_NAME_POWER,
                VIVO_KEY_WORD_H_NAME: HA_ATTR_NAME_POWER,
                "v2h_converter": self.v2h_onoff,
                "h2v_converter": self.h2v_onoff,
            },
            # home
            {
                VIVO_KEY_WORD_V_NAME: VIVO_ATTR_NAME_HOME,
                VIVO_KEY_WORD_H_NAME: HA_ATTR_NAME_HOME,
                "v2h_converter": self.v2h_home,
                "h2v_converter": self.h2v_home,
            },
            # menu
            {
                VIVO_KEY_WORD_V_NAME: VIVO_ATTR_NAME_MENU,
                VIVO_KEY_WORD_H_NAME: HA_ATTR_NAME_MENU,
                "v2h_converter": self.v2h_menu,
                "h2v_converter": self.h2v_menu,
            },

            # enter
            {
                VIVO_KEY_WORD_V_NAME: VIVO_ATTR_NAME_ENTER,
                VIVO_KEY_WORD_H_NAME: HA_ATTR_NAME_ENTER,
                "v2h_converter": self.v2h_enter,
                "h2v_converter": self.h2v_enter,
            },

            # back
            {
                VIVO_KEY_WORD_V_NAME: VIVO_ATTR_NAME_BACK,
                VIVO_KEY_WORD_H_NAME: HA_ATTR_NAME_BACK,
                "v2h_converter": self.v2h_back,
                "h2v_converter": self.h2v_back,
            },
            # left
            {
                VIVO_KEY_WORD_V_NAME: VIVO_ATTR_NAME_LEFT,
                VIVO_KEY_WORD_H_NAME: HA_ATTR_NAME_LEFT,
                "v2h_converter": self.v2h_left,
                "h2v_converter": self.h2v_left,
            },
            # right
            {
                VIVO_KEY_WORD_V_NAME: VIVO_ATTR_NAME_RIGHT,
                VIVO_KEY_WORD_H_NAME: HA_ATTR_NAME_RIGHT,
                "v2h_converter": self.v2h_right,
                "h2v_converter": self.h2v_right,
            },
            # up
            {
                VIVO_KEY_WORD_V_NAME: VIVO_ATTR_NAME_UP,
                VIVO_KEY_WORD_H_NAME: HA_ATTR_NAME_UP,
                "v2h_converter": self.v2h_up,
                "h2v_converter": self.h2v_up,
            },
            # down
            {
                VIVO_KEY_WORD_V_NAME: VIVO_ATTR_NAME_DOWN,
                VIVO_KEY_WORD_H_NAME: HA_ATTR_NAME_DOWN,
                "v2h_converter": self.v2h_down,
                "h2v_converter": self.h2v_down,
            },
            # volume set
            {
                VIVO_KEY_WORD_V_NAME: VIVO_ATTR_NAME_VOLUME,
                VIVO_KEY_WORD_H_NAME: HA_ATTR_NAME_VOLUME,
                "v2h_converter": self.v2h_volumn_level_set,
                "h2v_converter": self.h2v_volumn_level_set,
            },
            # volume up
            {
                VIVO_KEY_WORD_V_NAME: VIVO_ATTR_NAME_VOLUME_UP,
                VIVO_KEY_WORD_H_NAME: HA_ATTR_NAME_VOLUME_UP,
                "v2h_converter": self.v2h_volumn_up,
                "h2v_converter": self.h2v_volumn_up,
            },
            # volume down
            {
                VIVO_KEY_WORD_V_NAME: VIVO_ATTR_NAME_VOLUME_DOWN,
                VIVO_KEY_WORD_H_NAME: HA_ATTR_NAME_VOLUME_DOWN,
                "v2h_converter": self.v2h_volumn_down,
                "h2v_converter": self.h2v_volumn_down,
            },
            # volume mute
            {
                VIVO_KEY_WORD_V_NAME: VIVO_ATTR_NAME_MUTE,
                VIVO_KEY_WORD_H_NAME: HA_ATTR_NAME_MUTE,
                "v2h_converter": self.v2h_volumn_mute,
                "h2v_converter": self.h2v_volumn_mute,
            },
            # play
            {
                VIVO_KEY_WORD_V_NAME: VIVO_ATTR_NAME_PLAY,
                VIVO_KEY_WORD_H_NAME: HA_ATTR_NAME_PLAY,
                "v2h_converter": self.v2h_play,
                "h2v_converter": self.h2v_play,
            },
            # pause
            {
                VIVO_KEY_WORD_V_NAME: VIVO_ATTR_NAME_PAUSE,
                VIVO_KEY_WORD_H_NAME: HA_ATTR_NAME_PAUSE,
                "v2h_converter": self.v2h_pause,
                "h2v_converter": self.h2v_pause,
            },
            # previous
            {
                VIVO_KEY_WORD_V_NAME: VIVO_ATTR_NAME_PREVIOUS,
                VIVO_KEY_WORD_H_NAME: HA_ATTR_NAME_PREVIOUS,
                "v2h_converter": self.v2h_previous,
                "h2v_converter": self.h2v_previous,
            },
            # next
            {
                VIVO_KEY_WORD_V_NAME: VIVO_ATTR_NAME_NEXT,
                VIVO_KEY_WORD_H_NAME: HA_ATTR_NAME_NEXT,
                "v2h_converter": self.v2h_next,
                "h2v_converter": self.h2v_next,
            },
            # stop
            {
                VIVO_KEY_WORD_V_NAME: VIVO_ATTR_NAME_STOP,
                VIVO_KEY_WORD_H_NAME: HA_ATTR_NAME_STOP,
                "v2h_converter": self.v2h_stop,
                "h2v_converter": self.h2v_stop,
            }
        ]

    def v2h_onoff(self, device_id: str, index: int, on_off: dict, val):
        """Turn off the tv."""
        VLog.info(_TAG, f"[v2h_onoff],val:{val}")
        service: str = "turn_on"
        h_attributes: dict = {"entity_id": device_id}
        if val == VIVO_ATTR_VALUE_POWER_OFF:
            service = "turn_off"
        elif val == VIVO_ATTR_VALUE_POWER_ON:
            service = "turn_on"
        else:
            VLog.warning(_TAG, f"[v2h_onoff],param is invalid, val:{val}")
            return None, None
        return service, h_attributes

    def h2v_onoff(self, device_id: str, index: int, on_off: dict, val):
        """返回开关状态."""
        VLog.info(_TAG, f"[h2v_onoff],val:{val}")
        if val == "turn_off":
            return VIVO_ATTR_VALUE_POWER_OFF
        return VIVO_ATTR_VALUE_POWER_ON

    # Home
    def v2h_home(self, device_id: str, index: int, on_off: dict, val):
        """Turn off the tv."""
        VLog.info(_TAG, f"[v2h_home],val:{val}")
        if val != VIVO_ATTR_VALUE_HOME:
            VLog.warning(_TAG, f"[v2h_home],param is invalid, val:{val}")
            return None, None
        h_attributes: dict = self._LG_COMMAND_PARAM
        h_attributes["entity_id"] = device_id
        h_attributes["button"] = HA_ATTR_VALUE_HOME.upper()
        return self._LG_SERVICE_COMMAND, h_attributes

    def h2v_home(self, device_id: str, index: int, on_off: dict, val):
        return VIVO_ATTR_VALUE_HOME

    # Menu
    def v2h_menu(self, device_id: str, index: int, on_off: dict, val):
        """Turn off the tv."""
        VLog.info(_TAG, f"[v2h_menu],val:{val}")
        if val != VIVO_ATTR_VALUE_MENU:
            VLog.warning(_TAG, f"[v2h_menu],param is invalid, val:{val}")
            return None, None
        h_attributes: dict = self._LG_COMMAND_PARAM
        h_attributes["entity_id"] = device_id
        h_attributes["button"] = HA_ATTR_VALUE_MENU.upper()
        return self._LG_SERVICE_COMMAND, h_attributes

    def h2v_menu(self, device_id: str, index: int, on_off: dict, val):
        return VIVO_ATTR_VALUE_HOME

    # enter
    def v2h_enter(self, device_id: str, index: int, on_off: dict, val):
        VLog.info(_TAG, f"[v2h_enter],val:{val}")
        if val != VIVO_ATTR_VALUE_ENTER:
            VLog.warning(_TAG, f"[v2h_enter],param is invalid, val:{val}")
            return None, None
        h_attributes: dict = self._LG_COMMAND_PARAM
        h_attributes["entity_id"] = device_id
        h_attributes["button"] = HA_ATTR_VALUE_ENTER.upper()
        return self._LG_SERVICE_COMMAND, h_attributes

    def h2v_enter(self, device_id: str, index: int, on_off: dict, val):
        return VIVO_ATTR_VALUE_ENTER

    # back
    def v2h_back(self, device_id: str, index: int, on_off: dict, val):
        VLog.info(_TAG, f"[v2h_back],val:{val}")
        if val != VIVO_ATTR_VALUE_BACK:
            VLog.warning(_TAG, f"[v2h_back],param is invalid, val:{val}")
            return None, None
        h_attributes: dict = self._LG_COMMAND_PARAM
        h_attributes["entity_id"] = device_id
        h_attributes["button"] = HA_ATTR_VALUE_BACK.upper()
        return self._LG_SERVICE_COMMAND, h_attributes

    def h2v_back(self, device_id: str, index: int, on_off: dict, val):
        return VIVO_ATTR_VALUE_BACK

    # left
    def v2h_left(self, device_id: str, index: int, on_off: dict, val):
        VLog.info(_TAG, f"[v2h_left],val:{val}")
        if val != VIVO_ATTR_VALUE_LEFT:
            VLog.warning(_TAG, f"[v2h_left],param is invalid, val:{val}")
            return None, None
        h_attributes: dict = self._LG_COMMAND_PARAM
        h_attributes["entity_id"] = device_id
        h_attributes["button"] = HA_ATTR_VALUE_LEFT.upper()
        return self._LG_SERVICE_COMMAND, h_attributes

    def h2v_left(self, device_id: str, index: int, on_off: dict, val):
        return VIVO_ATTR_VALUE_LEFT

    # right
    def v2h_right(self, device_id: str, index: int, on_off: dict, val):
        VLog.info(_TAG, f"[v2h_right],val:{val}")
        if val != VIVO_ATTR_VALUE_RIGHT:
            VLog.warning(_TAG, f"[v2h_right],param is invalid, val:{val}")
            return None, None
        h_attributes: dict = self._LG_COMMAND_PARAM
        h_attributes["entity_id"] = device_id
        h_attributes["button"] = HA_ATTR_VALUE_RIGHT.upper()
        return self._LG_SERVICE_COMMAND, h_attributes

    def h2v_right(self, device_id: str, index: int, on_off: dict, val):
        return VIVO_ATTR_VALUE_RIGHT

    # up
    def v2h_up(self, device_id: str, index: int, on_off: dict, val):
        VLog.info(_TAG, f"[v2h_up],val:{val}")
        if val != VIVO_ATTR_VALUE_UP:
            VLog.warning(_TAG, f"[v2h_up],param is invalid, val:{val}")
            return None, None
        h_attributes: dict = self._LG_COMMAND_PARAM
        h_attributes["entity_id"] = device_id
        h_attributes["button"] = HA_ATTR_VALUE_UP.upper()
        return self._LG_SERVICE_COMMAND, h_attributes

    def h2v_up(self, device_id: str, index: int, on_off: dict, val):
        return VIVO_ATTR_VALUE_UP

    # down
    def v2h_down(self, device_id: str, index: int, on_off: dict, val):
        VLog.info(_TAG, f"[v2h_down],val:{val}")
        if val != VIVO_ATTR_VALUE_DOWN:
            VLog.warning(_TAG, f"[v2h_down],param is invalid, val:{val}")
            return None, None
        h_attributes: dict = self._LG_COMMAND_PARAM
        h_attributes["entity_id"] = device_id
        h_attributes["button"] = HA_ATTR_VALUE_DOWN.upper()
        return self._LG_SERVICE_COMMAND, h_attributes

    def h2v_down(self, device_id: str, index: int, on_off: dict, val):
        return VIVO_ATTR_VALUE_DOWN

    def v2h_volumn_level_set(self, device_id: str, index: int, on_off: dict, val):
        service: str = SERVICE_VOLUME_SET
        h_attributes: dict = {}
        VLog.info(_TAG, f"[v2h_volumn_level_set],val:{val}")
        h_attributes["entity_id"] = device_id
        if val <= 0:
            h_attributes[ATTR_MEDIA_VOLUME_LEVEL] = 0.0
        elif val >= 100:
            h_attributes[ATTR_MEDIA_VOLUME_LEVEL] = 1.0
        else:
            h_attributes[ATTR_MEDIA_VOLUME_LEVEL] = val / 100.0
        return service, h_attributes

    def h2v_volumn_level_set(self, device_id: str, index: int, on_off: dict, val):
        VLog.info(_TAG, f"[h2v_volumn_level_set],val:{val}")
        if val <= 0:
            return 0
        if val >= 1:
            return 100
        return round(val * 100)

    def v2h_volumn_up(self, device_id: str, index: int, on_off: dict, val):
        if val != VIVO_ATTR_VALUE_VOLUME_UP:
            VLog.warning(_TAG, f"[v2h_volumn_up],param is invalid, val:{val}")
            return None, None
        """ media play 
        service: str = SERVICE_VOLUME_UP
        h_attributes: dict = {}
        VLog.info(_TAG, f"[],val:{val}")
        h_attributes["entity_id"] = device_id
        return service, h_attributes
        """
        """button"""
        VLog.info(_TAG, f"[v2h_volumn_up],val:{val}")
        h_attributes: dict = self._LG_COMMAND_PARAM
        h_attributes["entity_id"] = device_id
        h_attributes["button"] = HA_LG_ATTR_NAME_VOLUME_UP.upper()
        return self._LG_SERVICE_COMMAND, h_attributes

    def h2v_volumn_up(self, device_id: str, index: int, on_off: dict, val):
        return VIVO_ATTR_VALUE_VOLUME_UP

    def v2h_volumn_down(self, device_id: str, index: int, on_off: dict, val):
        if val != VIVO_ATTR_VALUE_VOLUME_DOWN:
            VLog.warning(_TAG, f"[v2h_volumn_down],param is invalid, val:{val}")
            return None, None
        """ media play 
        service: str = SERVICE_VOLUME_DOWN
        h_attributes: dict = {}
        VLog.info(_TAG, f"[],val:{val}")
        h_attributes["entity_id"] = device_id
        return service, h_attributes
        """
        """button"""
        VLog.info(_TAG, f"[v2h_volumn_down],val:{val}")
        h_attributes: dict = self._LG_COMMAND_PARAM
        h_attributes["entity_id"] = device_id
        h_attributes["button"] = HA_LG_ATTR_NAME_VOLUME_DOWN.upper()
        return self._LG_SERVICE_COMMAND, h_attributes

    def h2v_volumn_down(self, device_id: str, index: int, on_off: dict, val):
        return VIVO_ATTR_VALUE_VOLUME_DOWN

    # mute
    def v2h_volumn_mute(self, device_id: str, index: int, on_off: dict, val):
        if val != VIVO_ATTR_VALUE_MUTE:
            VLog.warning(_TAG, f"[v2h_volumn_mute],param is invalid, val:{val}")
            return None, None
        """ media play 
        service: str = SERVICE_VOLUME_MUTE
        h_attributes: dict = {}
        VLog.info(_TAG, f"[],val:{val}")
        h_attributes["entity_id"] = device_id
        return service, h_attributes
        """
        """button"""
        VLog.info(_TAG, f"[v2h_volumn_mute],val:{val}")
        h_attributes: dict = self._LG_COMMAND_PARAM
        h_attributes["entity_id"] = device_id
        h_attributes["button"] = HA_ATTR_NAME_MUTE.upper()
        return self._LG_SERVICE_COMMAND, h_attributes

    def h2v_volumn_mute(self, device_id: str, index: int, on_off: dict, val):
        return VIVO_ATTR_VALUE_MUTE

    # play
    def v2h_play(self, device_id: str, index: int, on_off: dict, val):
        if val != VIVO_ATTR_VALUE_PLAY:
            VLog.warning(_TAG, f"[v2h_play],param is invalid, val:{val}")
            return None, None
        """ media play 
        service: str = SERVICE_MEDIA_PLAY
        h_attributes: dict = {}
        VLog.info(_TAG, f"[],val:{val}")
        h_attributes["entity_id"] = device_id
        return service, h_attributes
        """
        """button"""
        VLog.info(_TAG, f"[v2h_play],val:{val}")
        h_attributes: dict = self._LG_COMMAND_PARAM
        h_attributes["entity_id"] = device_id
        h_attributes["button"] = HA_ATTR_NAME_PLAY.upper()
        return self._LG_SERVICE_COMMAND, h_attributes

    def h2v_play(self, device_id: str, index: int, on_off: dict, val):
        return VIVO_ATTR_VALUE_PLAY

    # pause
    def v2h_pause(self, device_id: str, index: int, on_off: dict, val):
        if val != VIVO_ATTR_VALUE_PAUSE:
            VLog.warning(_TAG, f"[v2h_pause],param is invalid, val:{val}")
            return None, None
        """ media play 
        service: str = SERVICE_MEDIA_PAUSE
        h_attributes: dict = {}
        VLog.info(_TAG, f"[],val:{val}")
        h_attributes["entity_id"] = device_id
        return service, h_attributes
        """
        """button"""
        VLog.info(_TAG, f"[v2h_pause],val:{val}")
        h_attributes: dict = self._LG_COMMAND_PARAM
        h_attributes["entity_id"] = device_id
        h_attributes["button"] = HA_ATTR_NAME_PAUSE.upper()
        return self._LG_SERVICE_COMMAND, h_attributes

    def h2v_pause(self, device_id: str, index: int, on_off: dict, val):
        return VIVO_ATTR_VALUE_PAUSE

    # previous
    def v2h_previous(self, device_id: str, index: int, on_off: dict, val):
        if val != VIVO_ATTR_VALUE_PREVIOUS:
            VLog.warning(_TAG, f"[v2h_previous],param is invalid, val:{val}")
            return None, None
        """button"""
        """
        VLog.info(_TAG, f"[],val:{val}")
        h_attributes: dict = self._LG_COMMAND_PARAM
        h_attributes["entity_id"] = device_id
        h_attributes["button"] = "CHANNELUP"
        return self._LG_SERVICE_COMMAND, h_attributes
        """
        service: str = SERVICE_MEDIA_PREVIOUS_TRACK
        h_attributes: dict = {}
        VLog.info(_TAG, f"[v2h_previous],val:{val}")
        h_attributes["entity_id"] = device_id
        return service, h_attributes

    def h2v_previous(self, device_id: str, index: int, on_off: dict, val):
        return VIVO_ATTR_VALUE_PAUSE

    # next
    def v2h_next(self, device_id: str, index: int, on_off: dict, val):
        if val != VIVO_ATTR_VALUE_NEXT:
            VLog.warning(_TAG, f"[v2h_next],param is invalid, val:{val}")
            return None, None
        """button"""
        """
        VLog.info(_TAG, f"[v2h_next],val:{val}")
        h_attributes: dict = self._LG_COMMAND_PARAM
        h_attributes["entity_id"] = device_id
        h_attributes["button"] = "CHANNELDOWN"
        return self._LG_SERVICE_COMMAND, h_attributes
        """
        """ media play"""
        service: str = SERVICE_MEDIA_NEXT_TRACK
        h_attributes: dict = {}
        VLog.info(_TAG, f"[v2h_next],val:{val}")
        h_attributes["entity_id"] = device_id
        return service, h_attributes

    def h2v_next(self, device_id: str, index: int, on_off: dict, val):
        return VIVO_ATTR_VALUE_NEXT

    # stop
    def v2h_stop(self, device_id: str, index: int, on_off: dict, val):
        if val != VIVO_ATTR_VALUE_STOP:
            VLog.warning(_TAG, f"[v2h_stop],param is invalid, val:{val}")
            return None, None
        service: str = SERVICE_MEDIA_STOP
        h_attributes: dict = {}
        VLog.info(_TAG, f"[v2h_stop],val:{val}")
        h_attributes["entity_id"] = device_id
        return service, h_attributes

    def h2v_stop(self, device_id: str, index: int, on_off: dict, val):
        return VIVO_ATTR_VALUE_STOP

    @classmethod
    def media_player_model_get(cls, device: dr.DeviceEntry, attributes: Mapping[str, Any]):
        try:
            VLog.info(_TAG, f"[lg_media_player_model_get] {device}\n json of attribute is {json.dumps(attributes,default=str)}")
        except Exception as e:
            VLog.warning(_TAG, f"<json error: {e}>")
        model: list = []
        _tv_common_model = cls.get_media_player_model_from_feature(device, attributes)
        try:
            VLog.info(_TAG, f"[lg_media_player_model_get] _tv_common_model {json.dumps(_tv_common_model,default=str)}", )
        except Exception as e:
            VLog.warning(_TAG, f"<json error: {e}>")
        model += _tv_common_model
        lg_keys_out_of_feature = ["left", "right", "down", "up", "home", "menu", "back", "enter",
                                  HA_LG_ATTR_NAME_VOLUME_UP, HA_LG_ATTR_NAME_VOLUME_DOWN,
                                  "play", "pause", "mute"]
        for h_key in lg_keys_out_of_feature:
            _item = VAttributeUtils.get_model_item(Platform.MEDIA_PLAYER, h_key)
            if _item is not None:
                model.append(_item)
        try:
            VLog.info(_TAG, f"[lg_media_player_model_get] models {json.dumps(model,default=str)}", )
        except Exception as e:
            VLog.warning(_TAG, f"<json error: {e}>")
        return model

    @staticmethod
    def remote_model_get(device: dr.DeviceEntry, attributes: Mapping[str, Any]):
        model: list = []
        return model

    @classmethod
    def get_media_player_model_from_feature(cls, device: dr.DeviceEntry, attributes: Mapping[str, Any]):
        platform_name = Platform.MEDIA_PLAYER
        model: list = []
        supported_feature = attributes.get("supported_features", 0)
        power_features = (
                MediaPlayerEntityFeature.TURN_ON
                | MediaPlayerEntityFeature.TURN_OFF
        )
        if supported_feature & power_features:
            power_model = VAttributeUtils.get_model_item(platform_name, HA_ATTR_NAME_POWER)
            if power_model is not None:
                model.append(power_model)
        if supported_feature & MediaPlayerEntityFeature.VOLUME_SET:
            volume_set_model = VAttributeUtils.get_model_item(platform_name, HA_ATTR_NAME_VOLUME)
            if volume_set_model is not None:
                model.append(volume_set_model)
        if supported_feature & MediaPlayerEntityFeature.NEXT_TRACK:
            next_track = VAttributeUtils.get_model_item(platform_name, HA_ATTR_NAME_NEXT)
            if next_track is not None:
                model.append(next_track)
        if supported_feature & MediaPlayerEntityFeature.PREVIOUS_TRACK:
            previous_track = VAttributeUtils.get_model_item(platform_name, HA_ATTR_NAME_PREVIOUS)
            if previous_track is not None:
                model.append(previous_track)
        return model


class VAppleTV(VTVCommon):
    BRAND_NAME = "Apple"

    _APPLE_SERVICE_COMMAND = "send_command"
    _APPLE_COMMAND_PARAM: dict = {"num_repeats": 1,
                                  "delay_secs": 0.4,
                                  "hold_secs": 0}

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, domain: str) -> None:
        super().__init__(hass, entry, domain)
        self.attributes_map = [
            {
                VIVO_KEY_WORD_V_NAME: VIVO_ATTR_NAME_POWER,
                VIVO_KEY_WORD_H_NAME: HA_ATTR_NAME_POWER,
                "v2h_converter": self.v2h_onoff,
                "h2v_converter": self.h2v_onoff,
            },
            # virtual remote control
            {
                VIVO_KEY_WORD_V_NAME: VIVO_ATTR_NAME_REMOTE_POWER,
                VIVO_KEY_WORD_H_NAME: HA_ATTR_NAME_REMOTE_POWER,
                "v2h_converter": self.v2h_control_onoff,
                "h2v_converter": self.h2v_control_onoff,
            },
            {
                VIVO_KEY_WORD_V_NAME: VIVO_ATTR_NAME_VOLUME,
                VIVO_KEY_WORD_H_NAME: HA_ATTR_NAME_VOLUME,
                "v2h_converter": self.v2h_volumn_level_set,
                "h2v_converter": self.h2v_volumn_level_set,
            },
            {
                VIVO_KEY_WORD_V_NAME: VIVO_ATTR_NAME_WAKE_UP,
                VIVO_KEY_WORD_H_NAME: HA_ATTR_NAME_WAKE_UP,
                "v2h_converter": self.v2h_wakeup,
                "h2v_converter": self.h2v_wakeup,
            },
            # suspend
            {
                VIVO_KEY_WORD_V_NAME: VIVO_ATTR_NAME_STOP,
                VIVO_KEY_WORD_H_NAME: HA_ATTR_NAME_STOP,
                "v2h_converter": self.v2h_stop,
                "h2v_converter": self.h2v_stop,
            },
            # "home"
            {
                VIVO_KEY_WORD_V_NAME: VIVO_ATTR_NAME_HOME,
                VIVO_KEY_WORD_H_NAME: HA_ATTR_NAME_HOME,
                "v2h_converter": self.v2h_home,
                "h2v_converter": self.h2v_home,
            },
            # "top_menu",
            {
                VIVO_KEY_WORD_V_NAME: VIVO_ATTR_NAME_TOP_MENU,
                VIVO_KEY_WORD_H_NAME: HA_ATTR_NAME_TOP_MENU,
                "v2h_converter": self.v2h_top_menu,
                "h2v_converter": self.h2v_top_menu,
            },
            # "back",
            {
                VIVO_KEY_WORD_V_NAME: VIVO_ATTR_NAME_BACK,
                VIVO_KEY_WORD_H_NAME: HA_ATTR_NAME_BACK,
                "v2h_converter": self.v2h_back,
                "h2v_converter": self.h2v_back,
            },
            # "select",
            {
                VIVO_KEY_WORD_V_NAME: VIVO_ATTR_NAME_ENTER,
                VIVO_KEY_WORD_H_NAME: HA_ATTR_NAME_ENTER,
                "v2h_converter": self.v2h_enter,
                "h2v_converter": self.h2v_enter,
            },
            # "play",
            {
                VIVO_KEY_WORD_V_NAME: VIVO_ATTR_NAME_PLAY,
                VIVO_KEY_WORD_H_NAME: HA_ATTR_NAME_PLAY,
                "v2h_converter": self.v2h_play,
                "h2v_converter": self.h2v_play,
            },
            # "pause",
            {
                VIVO_KEY_WORD_V_NAME: VIVO_ATTR_NAME_PAUSE,
                VIVO_KEY_WORD_H_NAME: HA_ATTR_NAME_PAUSE,
                "v2h_converter": self.v2h_pause,
                "h2v_converter": self.h2v_pause,
            },
            # "up",
            {
                VIVO_KEY_WORD_V_NAME: VIVO_ATTR_NAME_UP,
                VIVO_KEY_WORD_H_NAME: HA_ATTR_NAME_UP,
                "v2h_converter": self.v2h_navigate_up,
                "h2v_converter": self.h2v_navigate_up,
            },
            # "down",
            {
                VIVO_KEY_WORD_V_NAME: VIVO_ATTR_NAME_DOWN,
                VIVO_KEY_WORD_H_NAME: HA_ATTR_NAME_DOWN,
                "v2h_converter": self.v2h_navigate_down,
                "h2v_converter": self.h2v_navigate_down,
            },
            # "left",
            {
                VIVO_KEY_WORD_V_NAME: VIVO_ATTR_NAME_LEFT,
                VIVO_KEY_WORD_H_NAME: HA_ATTR_NAME_LEFT,
                "v2h_converter": self.v2h_navigate_left,
                "h2v_converter": self.h2v_navigate_left,
            },
            # "right",
            {
                VIVO_KEY_WORD_V_NAME: VIVO_ATTR_NAME_RIGHT,
                VIVO_KEY_WORD_H_NAME: HA_ATTR_NAME_RIGHT,
                "v2h_converter": self.v2h_navigate_right,
                "h2v_converter": self.h2v_navigate_right,
            },
            # "volume_up",
            {
                VIVO_KEY_WORD_V_NAME: VIVO_ATTR_NAME_VOLUME_UP,
                VIVO_KEY_WORD_H_NAME: HA_ATTR_NAME_VOLUME_UP,
                "v2h_converter": self.v2h_volume_up,
                "h2v_converter": self.h2v_volume_up,
            },
            # "volume_down",
            {
                VIVO_KEY_WORD_V_NAME: VIVO_ATTR_NAME_VOLUME_DOWN,
                VIVO_KEY_WORD_H_NAME: HA_ATTR_NAME_VOLUME_DOWN,
                "v2h_converter": self.v2h_volume_down,
                "h2v_converter": self.h2v_volume_down,
            },
            # "previous",
            {
                VIVO_KEY_WORD_V_NAME: VIVO_ATTR_NAME_PREVIOUS,
                VIVO_KEY_WORD_H_NAME: HA_ATTR_NAME_PREVIOUS,
                "v2h_converter": self.v2h_navigate_previous,
                "h2v_converter": self.h2v_navigate_previous,
            },
            # "next",
            {
                VIVO_KEY_WORD_V_NAME: VIVO_ATTR_NAME_NEXT,
                VIVO_KEY_WORD_H_NAME: HA_ATTR_NAME_NEXT,
                "v2h_converter": self.v2h_navigate_next,
                "h2v_converter": self.h2v_navigate_next,
            }
        ]

    def v2h_onoff(self, device_id: str, index: int, on_off: dict, val):
        """Turn off the tv."""
        VLog.info(_TAG, f"[v2h_onoff], val:{val}")
        h_attributes: dict = self._APPLE_COMMAND_PARAM
        h_attributes["entity_id"] = device_id
        if val == VIVO_ATTR_VALUE_POWER_ON:
            h_attributes["command"] = SERVICE_TURN_ON
        elif val == VIVO_ATTR_VALUE_POWER_OFF:
            h_attributes["command"] = SERVICE_TURN_OFF
        else:
            VLog.warning(_TAG, f"[v2h_onoff],param is invalid, val:{val}")
            return None, None
        return self._APPLE_SERVICE_COMMAND, h_attributes

    def h2v_onoff(self, device_id: str, index: int, on_off: dict, val):
        """返回开关状态."""
        VLog.info(_TAG, f"[h2v_onoff],val:{val}")
        if val == SERVICE_TURN_OFF:
            return VIVO_ATTR_VALUE_POWER_OFF
        return VIVO_ATTR_VALUE_POWER_ON

    def v2h_control_onoff(self, device_id: str, index: int, on_off: dict, val):
        """remote control Turn on/off the tv."""
        VLog.info(_TAG, f"[v2h_control_onoff], val:{val}")
        service: str = SERVICE_TURN_ON
        h_attributes: dict = {"entity_id": device_id}
        if val == VIVO_ATTR_VALUE_REMOTE_POWER_OFF:
            service = SERVICE_TURN_OFF
        elif val == VIVO_ATTR_VALUE_REMOTE_POWER_ON:
            service = SERVICE_TURN_ON
        else:
            VLog.warning(_TAG, f"[v2h_control_onoff],param is invalid, val:{val}")
            return None, None
        return service, h_attributes

    def h2v_control_onoff(self, device_id: str, index: int, on_off: dict, val):
        """返回开关状态."""
        VLog.info(_TAG, f"[h2v_control_onoff],val:{val}")
        if val == SERVICE_TURN_OFF:
            return VIVO_ATTR_VALUE_REMOTE_POWER_OFF
        return VIVO_ATTR_VALUE_REMOTE_POWER_ON

    def h2v_volumn_level_set(self, device_id: str, index: int, on_off: dict, val):
        VLog.info(_TAG, f"[h2v_volumn_level_set],val:{val}")
        if val <= 0:
            return 0
        if val >= 1:
            return 100
        return round(val * 100)

    def v2h_volumn_level_set(self, device_id: str, index: int, on_off: dict, val):
        service: str = SERVICE_VOLUME_SET
        h_attributes: dict = {}
        VLog.info(_TAG, f"[v2h_volumn_level_set],val:{val}")
        h_attributes["entity_id"] = device_id
        if val <= 0:
            h_attributes[ATTR_MEDIA_VOLUME_LEVEL] = 0.0
        elif val >= 100:
            h_attributes[ATTR_MEDIA_VOLUME_LEVEL] = 1.0
        else:
            h_attributes[ATTR_MEDIA_VOLUME_LEVEL] = val / 100.0
        return service, h_attributes

    def v2h_wakeup(self, device_id: str, index: int, attribute: dict, val):
        VLog.info(_TAG, f"[v2h_wakeup], val:{val}")
        if val != VIVO_ATTR_VALUE_WAKE_UP:
            return None, None
        h_attributes: dict = self._APPLE_COMMAND_PARAM
        h_attributes["entity_id"] = device_id
        h_attributes["command"] = HA_ATTR_VALUE_WAKE_UP
        return self._APPLE_SERVICE_COMMAND, h_attributes

    def h2v_wakeup(self, device_id: str, index: int, on_off: dict, val):
        return VIVO_ATTR_VALUE_WAKE_UP

    def v2h_stop(self, device_id: str, index: int, attribute: dict, val):
        VLog.info(_TAG, f"[v2h_stop], val:{val}")
        if val != VIVO_ATTR_VALUE_STOP:
            return None, None
        h_attributes: dict = self._APPLE_COMMAND_PARAM
        h_attributes["entity_id"] = device_id
        h_attributes["command"] = HA_ATTR_VALUE_STOP
        return self._APPLE_SERVICE_COMMAND, h_attributes

    def h2v_stop(self, device_id: str, index: int, on_off: dict, val):
        return VIVO_ATTR_VALUE_STOP

    def v2h_home(self, device_id: str, index: int, attribute: dict, val):
        VLog.info(_TAG, f"[v2h_home], val:{val}")
        if val != VIVO_ATTR_VALUE_HOME:
            return None, None
        h_attributes: dict = self._APPLE_COMMAND_PARAM
        h_attributes["entity_id"] = device_id
        h_attributes["command"] = HA_ATTR_VALUE_HOME
        return self._APPLE_SERVICE_COMMAND, h_attributes

    def h2v_home(self, device_id: str, index: int, on_off: dict, val):
        return VIVO_ATTR_VALUE_HOME

    def v2h_top_menu(self, device_id: str, index: int, attribute: dict, val):
        VLog.info(_TAG, f"[v2h_top_menu], val:{val}")
        if val != VIVO_ATTR_VALUE_TOP_MENU:
            return None, None
        h_attributes: dict = self._APPLE_COMMAND_PARAM
        h_attributes["entity_id"] = device_id
        h_attributes["command"] = HA_ATTR_VALUE_TOP_MENU
        return self._APPLE_SERVICE_COMMAND, h_attributes

    def h2v_top_menu(self, device_id: str, index: int, on_off: dict, val):
        return VIVO_ATTR_VALUE_TOP_MENU

    def v2h_back(self, device_id: str, index: int, attribute: dict, val):
        VLog.info(_TAG, f"[v2h_back], val:{val}")
        if val != VIVO_ATTR_VALUE_BACK:
            return None, None
        h_attributes: dict = self._APPLE_COMMAND_PARAM
        h_attributes["entity_id"] = device_id
        h_attributes["command"] = HA_ATTR_VALUE_MENU
        return self._APPLE_SERVICE_COMMAND, h_attributes

    def h2v_back(self, device_id: str, index: int, on_off: dict, val):
        return VIVO_ATTR_VALUE_BACK

    def v2h_enter(self, device_id: str, index: int, attribute: dict, val):
        VLog.info(_TAG, f"[v2h_enter], val:{val}")
        if val != VIVO_ATTR_VALUE_ENTER:
            return None, None
        h_attributes: dict = self._APPLE_COMMAND_PARAM
        h_attributes["entity_id"] = device_id
        h_attributes["command"] = HA_APPLE_ATTR_VALUE_ENTER
        return self._APPLE_SERVICE_COMMAND, h_attributes

    def h2v_enter(self, device_id: str, index: int, on_off: dict, val):
        return VIVO_ATTR_VALUE_ENTER

    def v2h_play(self, device_id: str, index: int, attribute: dict, val):
        VLog.info(_TAG, f"[v2h_play], val:{val}")
        if val != VIVO_ATTR_VALUE_PLAY:
            return None, None
        h_attributes: dict = self._APPLE_COMMAND_PARAM
        h_attributes["entity_id"] = device_id
        h_attributes["command"] = HA_ATTR_VALUE_PLAY
        return self._APPLE_SERVICE_COMMAND, h_attributes

    def h2v_play(self, device_id: str, index: int, on_off: dict, val):
        return VIVO_ATTR_VALUE_PLAY

    def v2h_pause(self, device_id: str, index: int, attribute: dict, val):
        VLog.info(_TAG, f"[v2h_pause], val:{val}")
        if val != VIVO_ATTR_VALUE_PAUSE:
            return None, None
        h_attributes: dict = self._APPLE_COMMAND_PARAM
        h_attributes["entity_id"] = device_id
        h_attributes["command"] = HA_ATTR_VALUE_PAUSE
        return self._APPLE_SERVICE_COMMAND, h_attributes

    def h2v_pause(self, device_id: str, index: int, on_off: dict, val):
        return VIVO_ATTR_VALUE_PAUSE

    def v2h_navigate_up(self, device_id: str, index: int, attribute: dict, val):
        VLog.info(_TAG, f"[v2h_navigate_up], val:{val}")
        if val != VIVO_ATTR_VALUE_UP:
            return None, None
        h_attributes: dict = self._APPLE_COMMAND_PARAM
        h_attributes["entity_id"] = device_id
        h_attributes["command"] = HA_ATTR_VALUE_UP
        return self._APPLE_SERVICE_COMMAND, h_attributes

    def h2v_navigate_up(self, device_id: str, index: int, on_off: dict, val):
        return VIVO_ATTR_VALUE_UP

    def v2h_navigate_left(self, device_id: str, index: int, attribute: dict, val):
        VLog.info(_TAG, f"[v2h_navigate_left], val:{val}")
        if val != VIVO_ATTR_VALUE_LEFT:
            return None, None
        h_attributes: dict = self._APPLE_COMMAND_PARAM
        h_attributes["entity_id"] = device_id
        h_attributes["command"] = HA_ATTR_VALUE_LEFT
        return self._APPLE_SERVICE_COMMAND, h_attributes

    def h2v_navigate_left(self, device_id: str, index: int, on_off: dict, val):
        return VIVO_ATTR_VALUE_LEFT

    def v2h_navigate_down(self, device_id: str, index: int, attribute: dict, val):
        VLog.info(_TAG, f"[v2h_navigate_down], val:{val}")
        if val != VIVO_ATTR_VALUE_DOWN:
            return None, None
        h_attributes: dict = self._APPLE_COMMAND_PARAM
        h_attributes["entity_id"] = device_id
        h_attributes["command"] = HA_ATTR_VALUE_DOWN
        return self._APPLE_SERVICE_COMMAND, h_attributes

    def h2v_navigate_down(self, device_id: str, index: int, on_off: dict, val):
        return VIVO_ATTR_VALUE_DOWN

    def v2h_navigate_right(self, device_id: str, index: int, attribute: dict, val):
        VLog.info(_TAG, f"[v2h_navigate_right], val:{val}")
        if val != VIVO_ATTR_VALUE_RIGHT:
            return None, None
        h_attributes: dict = self._APPLE_COMMAND_PARAM
        h_attributes["entity_id"] = device_id
        h_attributes["command"] = HA_ATTR_VALUE_RIGHT
        return self._APPLE_SERVICE_COMMAND, h_attributes

    def h2v_navigate_right(self, device_id: str, index: int, on_off: dict, val):
        return VIVO_ATTR_VALUE_RIGHT

    def v2h_volume_up(self, device_id: str, index: int, attribute: dict, val):
        VLog.info(_TAG, f"[v2h_volume_up], val:{val}")
        if val != VIVO_ATTR_VALUE_VOLUME_UP:
            return None, None
        h_attributes: dict = self._APPLE_COMMAND_PARAM
        h_attributes["entity_id"] = device_id
        h_attributes["command"] = HA_ATTR_VALUE_VOLUME_UP
        return self._APPLE_SERVICE_COMMAND, h_attributes

    def h2v_volume_up(self, device_id: str, index: int, on_off: dict, val):
        return VIVO_ATTR_VALUE_VOLUME_UP

    def v2h_volume_down(self, device_id: str, index: int, attribute: dict, val):
        VLog.info(_TAG, f"[v2h_volume_down], val:{val}")
        if val != VIVO_ATTR_VALUE_VOLUME_DOWN:
            return None, None
        h_attributes: dict = self._APPLE_COMMAND_PARAM
        h_attributes["entity_id"] = device_id
        h_attributes["command"] = HA_ATTR_VALUE_VOLUME_DOWN
        return self._APPLE_SERVICE_COMMAND, h_attributes

    def h2v_volume_down(self, device_id: str, index: int, on_off: dict, val):
        return VIVO_ATTR_VALUE_VOLUME_DOWN

    def v2h_navigate_previous(self, device_id: str, index: int, attribute: dict, val):
        VLog.info(_TAG, f"[v2h_navigate_previous], val:{val}")
        if val != VIVO_ATTR_VALUE_PREVIOUS:
            return None, None
        h_attributes: dict = self._APPLE_COMMAND_PARAM
        h_attributes["entity_id"] = device_id
        h_attributes["command"] = HA_ATTR_VALUE_PREVIOUS
        return self._APPLE_SERVICE_COMMAND, h_attributes

    def h2v_navigate_previous(self, device_id: str, index: int, on_off: dict, val):
        return VIVO_ATTR_VALUE_PREVIOUS

    def v2h_navigate_next(self, device_id: str, index: int, attribute: dict, val):
        VLog.info(_TAG, f"[v2h_navigate_next], val:{val}")
        if val != VIVO_ATTR_VALUE_NEXT:
            return None, None
        h_attributes: dict = self._APPLE_COMMAND_PARAM
        h_attributes["entity_id"] = device_id
        h_attributes["command"] = HA_ATTR_VALUE_NEXT
        return self._APPLE_SERVICE_COMMAND, h_attributes

    def h2v_navigate_next(self, device_id: str, index: int, on_off: dict, val):
        return VIVO_ATTR_VALUE_NEXT

    @classmethod
    def media_player_model_get(cls, device: dr.DeviceEntry, attributes: Mapping[str, Any]):
        VLog.info(_TAG, "[apple_media_player_model_get] empty")
        model: list = []
        return model

    @staticmethod
    def remote_model_get(device: dr.DeviceEntry, attributes: Mapping[str, Any]):
        model: list = []
        h_key_world_tab = ["home", "top_menu", "select", "play", "pause", "up", "down",
                           "left",
                           "right", "volume_up", "volume_down", "previous", "next"]
        h_ext_key_woorld_tab = ["power", HA_ATTR_NAME_REMOTE_POWER, "back"]
        for h_key in h_key_world_tab:
            _item = VAttributeUtils.get_model_item(Platform.REMOTE, h_key)
            if _item is not None:
                model.append(_item)
        for h_ext_key in h_ext_key_woorld_tab:
            _item = VAttributeUtils.get_model_item(Platform.REMOTE, h_ext_key)
            if _item is not None:
                model.append(_item)
        try:
            VLog.info(_TAG, f"[remote_model_get] {json.dumps(model,default=str)}")
        except Exception as e:
            VLog.warning(_TAG, f"<json error: {e}>")
        return model

    @staticmethod
    def get_refined_v_power_attributes_dict(current_onoff: str, original_v_attributes: dict):
        """original_v_attributes """
        _power_set_state = original_v_attributes.get(VIVO_ATTR_NAME_POWER, None)
        if _power_set_state is None:
            VLog.info(_TAG, f"[get_refined_v_power_attributes_dict] stats is {original_v_attributes}")
            return original_v_attributes
        _power_set_state_result: dict = {}
        if current_onoff == VIVO_ATTR_VALUE_POWER_OFF:
            if _power_set_state == VIVO_ATTR_VALUE_POWER_ON:
                _power_set_state_result[VIVO_ATTR_NAME_REMOTE_POWER] = VIVO_ATTR_VALUE_REMOTE_POWER_ON
                for key, value in original_v_attributes.items():
                    _power_set_state_result[key] = value
                return _power_set_state_result
            else:
                VLog.info(_TAG, "[get_refined_v_power_attributes_dict] expect to off,but now is off")
                return None
        else:
            if _power_set_state == VIVO_ATTR_VALUE_POWER_ON:
                VLog.info(_TAG, "[get_refined_v_power_attributes_dict] expect to on,but now is on")
                return None
            else:
                for key, value in original_v_attributes.items():
                    _power_set_state_result[key] = value
                _power_set_state_result[VIVO_ATTR_NAME_REMOTE_POWER] = VIVO_ATTR_VALUE_REMOTE_POWER_OFF
            return _power_set_state_result


class VTVModelUtils:
    @classmethod
    def get_remote_device_attribute_list(cls, entity_id: str, hass: HomeAssistant, tv: VTVModel):
        if entity_id is None:
            return None
        _entity_obj = er.async_get(hass).async_get(entity_id)
        if _entity_obj is None or _entity_obj.device_id is None:
            VLog.info(_TAG, f"[get_remote_device_attribute_list] {entity_id} no device id")
            return None
        _device_id = _entity_obj.device_id
        _device = dr.async_get(hass).async_get(_device_id)
        _identify_name = next(iter(_device.identifiers))[0]
        VLog.info(_TAG, f"[get_remote_device_attribute_list] device id {_device_id}, name {_device.name}, "
                        f"identified {_identify_name}")
        _attributes_list = None
        if _identify_name == VTVModel.LG_IDENTIFIER_ID and _device.manufacturer == VLGTV.BRAND_NAME:
            _attributes_list = tv.vLGTV.attributes_map
        elif _identify_name == VTVModel.APPLE_IDENTIFIER_ID and _device.manufacturer == VAppleTV.BRAND_NAME:
            _attributes_list = tv.vAppleTV.attributes_map
        else:
            VLog.warning(_TAG, f"[get_remote_device_attribute_list] not supported remote {_identify_name} "
                               f"for {_device.manufacturer}")
        return _attributes_list

    @classmethod
    def get_media_player_attributes_list(cls, entity_id: str, hass: HomeAssistant, tv: VTVModel):
        if entity_id is None:
            return None
        _entity_obj = er.async_get(hass).async_get(entity_id)
        if _entity_obj is None or _entity_obj.device_id is None:
            VLog.info(_TAG, f"[get_media_player_attributes_list] {entity_id} no device id")
            return None
        _device_id = _entity_obj.device_id
        _device = dr.async_get(hass).async_get(_device_id)
        _identify_name = next(iter(_device.identifiers))[0]
        VLog.info(_TAG, f"[get_media_player_attributes_list] device id {_device_id}, name {_device.name}, "
                        f"identified {_identify_name}")
        _attributes_list = None
        if _identify_name == VTVModel.LG_IDENTIFIER_ID and _device.manufacturer == VLGTV.BRAND_NAME:
            _attributes_list = tv.vLGTV.attributes_map
        elif _identify_name == VTVModel.APPLE_IDENTIFIER_ID and _device.manufacturer == VAppleTV.BRAND_NAME:
            _attributes_list = tv.vAppleTV.attributes_map
        else:
            VLog.warning(_TAG, f"[get_media_player_attributes_list] not supported remote {_identify_name} "
                               f"for {_device.manufacturer}")
        return _attributes_list

    @classmethod
    def get_media_player_attribute_list_and_state(cls, entity_id: str, old_idle_state: str, new_idle_state: str,
                                                  hass: HomeAssistant, tv: VTVModel):
        if entity_id is None:
            VLog.warning(_TAG, "[get_media_player_device_attribute_list_and_state] entity_id is empty")
            return None, None
        _attributes_list = cls.get_media_player_attributes_list(entity_id, hass, tv)
        _current_attrs: dict = {}
        if old_idle_state != new_idle_state:
            VLog.info(_TAG, f"[get_media_player_attribute_list_and_state]stage change to {new_idle_state}")
            _current_attrs[HA_ATTR_NAME_POWER] = new_idle_state
        return _current_attrs, _attributes_list

    @classmethod
    def get_remote_attribute_list_and_state(cls, entity_id: str, old_idle_state: str, new_idle_state: str,
                                            hass: HomeAssistant, tv: VTVModel):
        if entity_id is None:
            VLog.warning(_TAG, "[get_remote_device_attribute_list_and_state]entity_id is empty")
            return None, None
        _attributes_list = cls.get_remote_device_attribute_list(entity_id, hass, tv)
        _current_attrs: dict = {}
        if old_idle_state != new_idle_state:
            VLog.info(_TAG, f"[get_remote_device_attribute_list_and_state]stage change to {new_idle_state}")
            _current_attrs[HA_ATTR_NAME_POWER] = new_idle_state
        return _current_attrs, _attributes_list

    @staticmethod
    def remote_model_get(device: dr.DeviceEntry, entity_attributes_map: Mapping[str, Any]):
        model: list = []
        VLog.info(_TAG, f"[remote_model_get] {device}")
        if device.manufacturer is None:
            VLog.warning(_TAG, "[remote_model_get] manufacturer is empty")
            return model
        _brand_name = next(iter(device.identifiers))[0]
        if _brand_name is None:
            VLog.warning(_TAG, "[remote_model_get] identifier is empty")
            return model
        if device.manufacturer == VLGTV.BRAND_NAME and _brand_name == VTVModel.LG_IDENTIFIER_ID:
            return VLGTV.remote_model_get(device, entity_attributes_map)
        elif device.manufacturer == VAppleTV.BRAND_NAME and _brand_name == VTVModel.APPLE_IDENTIFIER_ID:
            return VAppleTV.remote_model_get(device, entity_attributes_map)
        else:
            VLog.warning(_TAG, f"[remote_model_get] not support for {device.manufacturer} remote")
            return model

    @staticmethod
    def media_play_model_get(device: dr.DeviceEntry, entity_attributes_map: Mapping[str, Any]):
        model: list = []
        VLog.info(_TAG, f"[media_player_model_get] {device}")
        if device.manufacturer is None:
            VLog.warning(_TAG, "[media_play_model_get] manufacturer is empty")
            return model
        _brand_name = next(iter(device.identifiers))[0]
        if _brand_name is None:
            VLog.warning(_TAG, "[media_play_model_get] identifier is empty")
            return model
        if device.manufacturer == VLGTV.BRAND_NAME and _brand_name == VTVModel.LG_IDENTIFIER_ID:
            return VLGTV.media_player_model_get(device, entity_attributes_map)
        elif device.manufacturer == VAppleTV.BRAND_NAME and _brand_name == VTVModel.APPLE_IDENTIFIER_ID:
            return VAppleTV.media_player_model_get(device, entity_attributes_map)
        else:
            VLog.warning(_TAG, f"[media_player_model_get] not support for {device.manufacturer} media_player")
            return model

    @classmethod
    def get_refined_v_attributes_dict(cls, entity_id: str, current_onoff: str, original_v_attributes: dict,
                                      hass: HomeAssistant):
        if current_onoff != VIVO_ATTR_VALUE_POWER_ON and current_onoff != VIVO_ATTR_VALUE_POWER_OFF:
            VLog.info(_TAG, f"[get_refined_v_attributes_dict] current_onoff {current_onoff}")
            return original_v_attributes
        if VIVO_ATTR_NAME_POWER not in original_v_attributes:
            return original_v_attributes
        if entity_id is None:
            return original_v_attributes
        _entity_obj = er.async_get(hass).async_get(entity_id)
        if _entity_obj is None or _entity_obj.device_id is None:
            VLog.warning(_TAG, f"[get_refined_v_attributes_dict] {entity_id} no device id")
            return original_v_attributes
        _device_id = _entity_obj.device_id
        _device = dr.async_get(hass).async_get(_device_id)
        _identify_name = next(iter(_device.identifiers))[0]
        VLog.info(_TAG, f"[get_refined_v_attributes_dict] device id {_device_id}, name {_device.name}, "
                        f"identified {_identify_name}")
        if _identify_name == VTVModel.LG_IDENTIFIER_ID and _device.manufacturer == VLGTV.BRAND_NAME:
            return original_v_attributes
        elif _identify_name == VTVModel.APPLE_IDENTIFIER_ID and _device.manufacturer == VAppleTV.BRAND_NAME:
            return VAppleTV.get_refined_v_power_attributes_dict(current_onoff, original_v_attributes)
        else:
            return original_v_attributes
