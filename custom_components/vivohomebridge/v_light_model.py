"""
 Copyright 2024 vivo Mobile Communication Co., Ltd.
 Licensed under the Apache License, Version 2.0 (the "License");

    http://www.apache.org/licenses/LICENSE-2.0
"""
import json
from typing import Mapping, Any

from .v_attribute import VIVO_KEY_WORD_V_NAME, VIVO_KEY_WORD_H_NAME
from .v_utils.vattributes_utils import VAttributeUtils
from .v_utils.vlog import VLog
from homeassistant.components.light import (
    ATTR_BRIGHTNESS, ATTR_RGB_COLOR, ATTR_COLOR_TEMP_KELVIN, SERVICE_TURN_OFF, SERVICE_TURN_ON,
    ATTR_SUPPORTED_COLOR_MODES, brightness_supported, color_supported, color_temp_supported
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_ENTITY_ID, Platform
from homeassistant.core import HomeAssistant

_TAG = "light"


class VLightModel:
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, domain: str) -> None:
        self.hass = hass
        self.entry = entry
        self.domain = domain
        self.attributes_map = [
            {
                VIVO_KEY_WORD_V_NAME: "vivo_std_power",
                VIVO_KEY_WORD_H_NAME: "power",
                "v2h_converter": self.v2h_onoff,
                "h2v_converter": self.h2v_onoff
            }, {
                VIVO_KEY_WORD_V_NAME: "vivo_std_brightness",
                VIVO_KEY_WORD_H_NAME: ATTR_BRIGHTNESS,
                "v2h_converter": self.v2h_brightness,
                "h2v_converter": self.h2v_brightness
            }, {
                VIVO_KEY_WORD_V_NAME: "vivo_std_color_rgb",
                VIVO_KEY_WORD_H_NAME: ATTR_RGB_COLOR,
                "v2h_converter": self.v2h_color_rgb,
                "h2v_converter": self.h2v_color_rgb
            }, {
                VIVO_KEY_WORD_V_NAME: "vivo_std_light_temperature",
                VIVO_KEY_WORD_H_NAME: ATTR_COLOR_TEMP_KELVIN,
                "v2h_converter": self.v2h_color_temp,
                "h2v_converter": self.h2v_color_temp
            }
        ]

    def v2h_onoff(self, device_id: str, index: int, on_off: dict, val):
        VLog.info(_TAG, f"[v2h_onoff],val:{val}")
        service: str = "turn_on"
        h_attributes: dict = {ATTR_ENTITY_ID: device_id}
        if val == "off":
            service = SERVICE_TURN_OFF
        else:
            service = SERVICE_TURN_ON
        return service, h_attributes

    def h2v_onoff(self, device_id: str, index: int, on_off: dict, val):
        VLog.info(_TAG, f"[h2v_onoff] {device_id} {index}: {val}")
        if val == 'off':
            return 'off'
        else:
            return 'on'

    def v2h_color_rgb(self, device_id: str, index: int, rgb: dict, val):
        VLog.info(_TAG,
                  f"[h2v_color_rgb] ha:{rgb[VIVO_KEY_WORD_H_NAME]}:{val} <= vivo:{rgb[VIVO_KEY_WORD_V_NAME]}:{val}")
        val = tuple(json.loads(val))
        service: str = SERVICE_TURN_ON
        h_attributes: dict = {ATTR_ENTITY_ID: device_id, ATTR_RGB_COLOR: val}
        return service, h_attributes

    def h2v_color_rgb(self, device_id: str, index: int, rgb: dict, val):
        VLog.info(_TAG,
                  f"[h2v_color_rgb] ha:{rgb[VIVO_KEY_WORD_H_NAME]}:{val} => vivo:{rgb[VIVO_KEY_WORD_V_NAME]}:{val}")
        return val

    def v2h_color_temp(self, device_id: str, index: int, color_temp: dict, val):
        VLog.info(_TAG, f"[v2h_color_temp] ha:{color_temp[VIVO_KEY_WORD_H_NAME]}:{val} "
                        f"<= vivo:{color_temp[VIVO_KEY_WORD_V_NAME]}:{val}")
        service: str = SERVICE_TURN_ON
        h_attributes: dict = {ATTR_ENTITY_ID: device_id, ATTR_COLOR_TEMP_KELVIN: val}
        return service, h_attributes

    def h2v_color_temp(self, device_id: str, index: int, color_temp: dict, val):
        VLog.info(_TAG, f"[h2v_color_temp] ha:{color_temp[VIVO_KEY_WORD_H_NAME]}:{val} "
                        f"=> vivo:{color_temp[VIVO_KEY_WORD_V_NAME]}:{val}")
        return val

    def v2h_brightness(self, device_id: str, index: int, brightness: dict, val):
        val = int(val)
        VLog.info(_TAG, f"[v2h_brightness] ha:{brightness[VIVO_KEY_WORD_H_NAME]}:{int((val * 255) / 100)} "
                        f"<= vivo:{brightness[VIVO_KEY_WORD_V_NAME]}:{val}")
        service: str = SERVICE_TURN_ON
        h_attributes: dict = {ATTR_ENTITY_ID: device_id, ATTR_BRIGHTNESS: round((val * 255) / 100)}
        return service, h_attributes

    def h2v_brightness(self, device_id: str, index: int, brightness: dict, val):
        VLog.info(_TAG, f"[h2v_brightness] ha:{brightness[VIVO_KEY_WORD_H_NAME]}:{val} "
                        f"=> vivo:{brightness[VIVO_KEY_WORD_V_NAME]}:{int((val * 100) / 255)}")
        return round((val * 100) / 255)

    @classmethod
    def model_get(
        cls, hass: HomeAssistant, entity_id: str, entity_attributes: Mapping[str, Any]
    ) -> list:
        VLog.info(
            _TAG, f"[model_get]{entity_id},entity_attributes = {entity_attributes}"
        )
        model: list = []
        _power_model = VAttributeUtils.get_model_item(Platform.LIGHT, "power")
        if _power_model is not None:
            model.append(_power_model)
        color_modes = (entity_attributes.get(ATTR_SUPPORTED_COLOR_MODES) or [])
        if brightness_supported(color_modes):
            h_key = "brightness"
            _brightness = VAttributeUtils.get_model_item(Platform.LIGHT, h_key)
            if _brightness is not None:
                model.append(_brightness)
        if color_supported(color_modes):
            h_key = "rgb_color"
            _rgb = VAttributeUtils.get_model_item(Platform.LIGHT, h_key)
            if _rgb is not None:
                model.append(_rgb)
        if color_temp_supported(color_modes):
            h_key = "color_temp_kelvin"
            _color_temp = VAttributeUtils.get_model_item(Platform.LIGHT, h_key)
            if _color_temp is not None:
                model.append(_color_temp)
        return model
