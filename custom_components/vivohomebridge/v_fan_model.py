"""
 Copyright 2024 vivo Mobile Communication Co., Ltd.
 Licensed under the Apache License, Version 2.0 (the "License");

    http://www.apache.org/licenses/LICENSE-2.0
"""
from typing import Mapping, Any

from homeassistant.components.fan import (
    SERVICE_SET_PRESET_MODE, ATTR_PRESET_MODE, SERVICE_OSCILLATE, ATTR_OSCILLATING,
    SERVICE_SET_PERCENTAGE, ATTR_PERCENTAGE, FanEntityFeature, ATTR_PERCENTAGE_STEP, ATTR_PRESET_MODES
)
from homeassistant.const import ATTR_ENTITY_ID, ATTR_SUPPORTED_FEATURES, Platform
from .v_attribute import VIVO_KEY_WORD_V_NAME, VIVO_KEY_WORD_H_NAME, FAN_SPEED_STEP, FAN_MAX_SPEED, FAN_MIN_SPEED
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .v_utils.vattributes_utils import VAttributeUtils
from .v_utils.vlog import VLog

_TAG = "fan"


class VFanModel:
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
                # 运行模式
                VIVO_KEY_WORD_V_NAME: "vivo_std_mode",
                VIVO_KEY_WORD_H_NAME: "preset_mode",
                "v2h_converter": self.v2h_fan_mode,
                "h2v_converter": self.h2v_fan_mode
            },
            {
                # 摇头
                VIVO_KEY_WORD_V_NAME: "vivo_std_swing",
                VIVO_KEY_WORD_H_NAME: "oscillating",
                "v2h_converter": self.v2h_swing_onoff,
                "h2v_converter": self.h2v_swing_onoff
            }, {
                # 风速
                VIVO_KEY_WORD_V_NAME: "vivo_std_speed_gear",
                VIVO_KEY_WORD_H_NAME: "percentage",
                "v2h_converter": self.v2h_fan_speed,
                "h2v_converter": self.h2v_fan_speed
            },
        ]

    def v2h_onoff(self, device_id: str, index: int, on_off: dict, val):
        """Turn off the climate."""
        VLog.info(_TAG, f"[v2h_onoff],val:{val}")
        service: str = "turn_on"
        h_attributes: dict = {ATTR_ENTITY_ID: device_id}
        if val == "off":
            service = "turn_off"
        else:
            service = "turn_on"
        return service, h_attributes

    def h2v_onoff(self, device_id: str, index: int, on_off: dict, val):
        """返回开关状态."""
        VLog.info(_TAG, f"[h2v_onoff],val:{val}")
        if val == 'off':
            return 'off'
        return 'on'

    def h2v_fan_mode(self, device_id: str, index: int, on_off: dict, val):
        VLog.info(_TAG, f"[h2v_fan_mode] val:{val}")
        return VAttributeUtils.h2v_mode_get_value(Platform.FAN, ATTR_PRESET_MODES, val)

    def v2h_fan_mode(self, device_id: str, index: int, on_off: dict, val):
        VLog.info(_TAG, f"[v2h_fan_mode] val:{val}")
        h_mode_key = ATTR_PRESET_MODES
        h_attr_key = ATTR_PRESET_MODE
        service: str = SERVICE_SET_PRESET_MODE
        h_attributes: dict = {ATTR_ENTITY_ID: device_id, h_attr_key: val}
        h_attributes = VAttributeUtils.v2h_mode_get_attr(h_mode_key, h_attr_key, val, Platform.FAN, h_attributes)
        return service, h_attributes

    def h2v_swing_onoff(self, device_id: str, index: int, on_off: dict, val):
        VLog.info(_TAG, f"[h2v_swing_onoff],val:{val}")
        if not val:
            return 'off'
        return 'on'

    def v2h_swing_onoff(self, device_id: str, index: int, on_off: dict, val):
        service: str = SERVICE_OSCILLATE
        h_attributes: dict = {}
        VLog.info(_TAG, f"[v2h_swing_onoff],val:{val}")
        h_attributes[ATTR_ENTITY_ID] = device_id
        if val == 'off':
            h_attributes[ATTR_OSCILLATING] = False
        else:
            h_attributes[ATTR_OSCILLATING] = True
        return service, h_attributes

    def h2v_fan_speed(self, device_id: str, index: int, on_off: dict, val):
        VLog.info(_TAG, f"[h2v_fan_speed],val:{val}")
        return val

    def v2h_fan_speed(self, device_id: str, index: int, on_off: dict, val):
        service: str = SERVICE_SET_PERCENTAGE
        h_attributes: dict = {}
        VLog.info(_TAG, f"[v2h_fan_speed],val:{val}")
        h_attributes[ATTR_ENTITY_ID] = device_id
        h_attributes[ATTR_PERCENTAGE] = val
        return service, h_attributes

    @classmethod
    def model_get(cls,hass: HomeAssistant, entity_id: str, entity_attributes: Mapping[str, Any]) -> list:
        model: list = []
        supported_features = entity_attributes.get(ATTR_SUPPORTED_FEATURES, 0)
        VLog.info(_TAG, f"[model_get] FanEntityFeature(self.supported_features)={FanEntityFeature(supported_features)}"
                        f"\n entity_attributes = {entity_attributes}")
        _power_mode = VAttributeUtils.get_model_item(Platform.FAN, "power")
        if _power_mode is not None:
            model.append(_power_mode)
        if (FanEntityFeature.SET_SPEED & FanEntityFeature(supported_features)) != 0:
            h_key = "percentage"
            VLog.info(_TAG, f"[model_get] {entity_id} support {h_key}")
            _percentage_model = VAttributeUtils.get_model_item(Platform.FAN, h_key)
            _percentage_step = entity_attributes.get(ATTR_PERCENTAGE_STEP, FAN_SPEED_STEP)
            if _percentage_model is not None:
                _percentage_model["value_range"] = [FAN_MIN_SPEED, FAN_MAX_SPEED, _percentage_step]
                model.append(_percentage_model)
        if (FanEntityFeature.OSCILLATE & FanEntityFeature(supported_features)) != 0:
            h_key = "oscillating"
            VLog.info(_TAG, f"[model_get] {entity_id} support {h_key}")
            _oscillating_model = VAttributeUtils.get_model_item(Platform.FAN, h_key)
            if _oscillating_model is not None:
                model.append(_oscillating_model)
        if (FanEntityFeature.DIRECTION & FanEntityFeature(supported_features)) != 0:
            h_key = "direction"
            VLog.info(_TAG, f"[model_get] {entity_id} support {h_key}")
        if (FanEntityFeature.PRESET_MODE & FanEntityFeature(supported_features)) != 0:
            h_key = ATTR_PRESET_MODES
            h_fan_modes: list = entity_attributes.get(h_key, None)
            if h_fan_modes is not None and len(h_fan_modes) > 0:
                v_fan_mode_dict: dict = VAttributeUtils.get_model_item(Platform.FAN, h_key)
                if v_fan_mode_dict is not None:
                    v_fan_mode_dict["value_list"] = VAttributeUtils.get_value_list(v_fan_mode_dict["value_list"],
                                                                                   h_fan_modes, [])
                    if v_fan_mode_dict["value_list"] is not None and len(v_fan_mode_dict["value_list"]) > 0:
                        VLog.info(_TAG, f"[model_get] {entity_id} support "
                                        f"{h_key}:{v_fan_mode_dict["value_list"]} fan_modes:{h_fan_modes}")
                        model.append(v_fan_mode_dict)
        return model
