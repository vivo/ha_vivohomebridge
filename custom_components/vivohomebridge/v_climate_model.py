"""
 Copyright 2024 vivo Mobile Communication Co., Ltd.
 Licensed under the Apache License, Version 2.0 (the "License");

    http://www.apache.org/licenses/LICENSE-2.0
"""
from typing import Mapping, Any

from homeassistant.const import ATTR_ENTITY_ID, ATTR_SUPPORTED_FEATURES, Platform
from .v_attribute import (
    VIVO_KEY_WORD_V_NAME, VIVO_KEY_WORD_H_NAME, VIVO_CLIMATE_SWING_MODE_VERTICAL_H_NAME,
    VIVO_CLIMATE_SWING_MODE_HORIZONTAL_H_NAME
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.components.climate import (
    ClimateEntityFeature,
    SWING_VERTICAL,
    SWING_HORIZONTAL,
    SERVICE_SET_FAN_MODE,
    SERVICE_SET_HVAC_MODE,
    SERVICE_SET_SWING_MODE,
    SERVICE_SET_TEMPERATURE,
    ATTR_MIN_TEMP,
    ATTR_MAX_TEMP,
    ATTR_TARGET_TEMP_STEP, ATTR_FAN_MODES, ATTR_MIN_HUMIDITY, ATTR_MAX_HUMIDITY, ATTR_SWING_MODE, ATTR_HVAC_MODE,
    ATTR_HVAC_MODES, ATTR_HVAC_ACTION, ATTR_FAN_MODE, ATTR_SWING_MODES, SWING_BOTH, SWING_OFF
)
from .utils import Utils
from .v_utils.vattributes_utils import VAttributeUtils
from .v_utils.vlog import VLog

CLIMATE_MIN_TEMP = 16
CLIMATE_MAX_TEMP = 32
CLIMATE_TEMP_STEP = 1
CLIMATE_MIN_HUMIDITY = 1
CLIMATE_MAX_HUMIDITY = 100
CLIMATE_HUMIDITY_STEP = 1
_TAG = "climate"


class VClimateModel:
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
            },
            {
                # 运行模式
                VIVO_KEY_WORD_V_NAME: "vivo_std_mode",
                VIVO_KEY_WORD_H_NAME: "state",
                "v2h_converter": self.v2h_hvac_mode,
                "h2v_converter": self.h2v_hvac_mode
            },
            {
                # 运行模式
                VIVO_KEY_WORD_V_NAME: "vivo_std_mode",
                VIVO_KEY_WORD_H_NAME: "air_conditioner.mode",
                "v2h_converter": self.v2h_hvac_mode,
                "h2v_converter": self.h2v_hvac_mode
            },
            {
                # 运行模式
                VIVO_KEY_WORD_V_NAME: "vivo_std_mode",
                VIVO_KEY_WORD_H_NAME: ATTR_HVAC_ACTION,
                "v2h_converter": self.v2h_hvac_mode,
                "h2v_converter": self.h2v_hvac_mode
            }, {
                # 目标温度
                VIVO_KEY_WORD_V_NAME: "vivo_std_temperature",
                VIVO_KEY_WORD_H_NAME: "temperature",
                "v2h_converter": self.v2h_target_temperature,
                "h2v_converter": self.h2v_target_temperature
            }, {
                # 风速
                VIVO_KEY_WORD_V_NAME: "vivo_std_wind_speed",
                VIVO_KEY_WORD_H_NAME: "fan_mode",
                "v2h_converter": self.v2h_fan_mode,
                "h2v_converter": self.h2v_fan_mode
            }, {
                # 上下摆风
                VIVO_KEY_WORD_V_NAME: "vivo_std_wind_swing_up_down",
                VIVO_KEY_WORD_H_NAME: VIVO_CLIMATE_SWING_MODE_VERTICAL_H_NAME,
                "h2v_converter": self.h2v_swing_mode_vertical,
                "v2h_converter": self.v2h_swing_mode_vertical
            }, {
                # 左右摆风
                VIVO_KEY_WORD_V_NAME: "vivo_std_wind_swing_left_right",
                VIVO_KEY_WORD_H_NAME: VIVO_CLIMATE_SWING_MODE_HORIZONTAL_H_NAME,
                "h2v_converter": self.h2v_swing_mode_horizontal,
                "v2h_converter": self.v2h_swing_mode_horizontal
            }, {
                # 当前温度
                VIVO_KEY_WORD_V_NAME: "vivo_std_indoor_temperature",
                VIVO_KEY_WORD_H_NAME: "current_temperature",
                "h2v_converter": self.h2v_current_temperature
            }, {
                # 当前湿度
                VIVO_KEY_WORD_V_NAME: "vivo_std_indoor_humidity",
                VIVO_KEY_WORD_H_NAME: "current_humidity",
                "h2v_converter": self.h2v_current_humidity
            }
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

    def h2v_hvac_mode(self, device_id: str, index: int, on_off: dict, val):
        VLog.info(_TAG, f"[h2v_hvac_mode],val:{val}")
        return VAttributeUtils.h2v_mode_get_value(Platform.CLIMATE, ATTR_HVAC_MODES, val)

    def v2h_hvac_mode(self, device_id: str, index: int, on_off: dict, val):
        VLog.info(_TAG, f"[v2h_hvac_mode] val:{val}")
        h_mode_key = ATTR_HVAC_MODES
        h_attr_key = ATTR_HVAC_MODE
        service: str = SERVICE_SET_HVAC_MODE
        h_attributes: dict = {ATTR_ENTITY_ID: device_id, h_attr_key: val}
        h_attributes = VAttributeUtils.v2h_mode_get_attr(h_mode_key, h_attr_key, val, Platform.CLIMATE, h_attributes)
        return service, h_attributes

    def h2v_target_temperature(self, device_id: str, index: int, on_off: dict, val):
        unit = Utils.get_entity_unit(self.hass, device_id)
        VLog.info(_TAG, f"[h2v_target_temperature] {device_id}  unit={unit} val:{val}")
        if unit == "°F":
            val = int(round((val - 32) * 5 / 9))
            VLog.info(_TAG, f"temperature unit is {unit} need to cover {val} °C")
        if unit == "K":
            val = int(round(val - 273.15))
            VLog.info(_TAG, f"temperature unit is {unit} need to cover {val} °C")
        return val

    def v2h_target_temperature(self, device_id: str, index: int, on_off: dict, val):
        unit = Utils.get_entity_unit(self.hass, device_id)
        VLog.info(_TAG, f"[v2h_target_temperature] {device_id}  unit={unit} val:{val}")
        if unit == "°F":
            val = float(val)
            val = int(round((val * 9 / 5) + 32))
            VLog.info(_TAG, f"temperature unit is {unit} need to cover {val} °F")
        if unit == "K":
            val = float(val)
            val = int(round(val + 273.15))
            VLog.info(_TAG, f"temperature unit is {unit} need to cover {val} K")
        service: str = SERVICE_SET_TEMPERATURE
        h_attributes: dict = {ATTR_ENTITY_ID: device_id, "temperature": val}
        return service, h_attributes

    def h2v_fan_mode(self, device_id: str, index: int, on_off: dict, val):
        VLog.info(_TAG, f"[h2v_fan_mode] val:{val}")
        return VAttributeUtils.h2v_mode_get_value(Platform.CLIMATE, ATTR_FAN_MODES, val)

    def v2h_fan_mode(self, device_id: str, index: int, on_off: dict, val):
        VLog.info(_TAG, f"[v2h_fan_mode] val:{val}")
        h_mode_key = ATTR_FAN_MODES
        h_attr_key = ATTR_FAN_MODE
        service: str = SERVICE_SET_FAN_MODE
        h_attributes: dict = {ATTR_ENTITY_ID: device_id, h_attr_key: val}
        h_attributes = VAttributeUtils.v2h_mode_get_attr(h_mode_key, h_attr_key, val, Platform.CLIMATE, h_attributes)
        return service, h_attributes

    def h2v_swing_mode_vertical(self, device_id: str, index: int, on_off: dict, val):
        swing_modes: list = self.hass.states.get(device_id).attributes.get(ATTR_SWING_MODES)
        VLog.info(_TAG, f"[h2v_swing_mode_vertical] val:{val} current swing_modes {swing_modes}")
        if SWING_VERTICAL not in swing_modes:
            return None
        # ['off', 'vertical', 'horizontal', 'both']
        if val == SWING_OFF or val == SWING_HORIZONTAL:
            return 'off'
        return 'on'

    def v2h_swing_mode_vertical(self, device_id: str, index: int, on_off: dict, val):
        service: str = SERVICE_SET_SWING_MODE
        h_attributes: dict = {ATTR_ENTITY_ID: device_id}
        swing_modes: list = self.hass.states.get(device_id).attributes.get(ATTR_SWING_MODES)
        # ['off', 'vertical', 'horizontal', 'both']
        current_swing_mode = self.hass.states.get(device_id).attributes.get(ATTR_SWING_MODE)
        VLog.info(_TAG, f"[v2h_swing_mode_vertical] val:{val} current {current_swing_mode} in {swing_modes}")
        if SWING_VERTICAL not in swing_modes:
            return None, None

        if val == SWING_OFF:
            if current_swing_mode == SWING_BOTH or current_swing_mode == SWING_HORIZONTAL:
                h_attributes[ATTR_SWING_MODE] = SWING_HORIZONTAL
            else:
                h_attributes[ATTR_SWING_MODE] = SWING_OFF
        else:
            if current_swing_mode == SWING_BOTH or current_swing_mode == SWING_HORIZONTAL:
                h_attributes[ATTR_SWING_MODE] = SWING_BOTH
            else:
                h_attributes[ATTR_SWING_MODE] = SWING_VERTICAL
        return service, h_attributes

    def h2v_swing_mode_horizontal(self, device_id: str, index: int, on_off: dict, val):
        swing_modes: list = self.hass.states.get(device_id).attributes.get(ATTR_SWING_MODES)
        VLog.info(_TAG, f"[h2v_swing_mode_horizontal] val:{val} current swing_modes {swing_modes}")
        if SWING_HORIZONTAL not in swing_modes:
            return None
        # ['off', 'vertical', 'horizontal', 'both']
        if val == SWING_OFF or val == SWING_VERTICAL:
            return 'off'
        return 'on'

    def v2h_swing_mode_horizontal(self, device_id: str, index: int, on_off: dict, val):
        service: str = SERVICE_SET_SWING_MODE
        h_attributes: dict = {ATTR_ENTITY_ID: device_id}
        swing_modes: list = self.hass.states.get(device_id).attributes.get(ATTR_SWING_MODES)
        # ['off', 'vertical', 'horizontal', 'both']
        current_swing_mode = self.hass.states.get(device_id).attributes.get(ATTR_SWING_MODE)
        VLog.info(_TAG, f"[v2h_swing_mode_horizontal] val:{val} current {current_swing_mode} in swing_modes {swing_modes}")
        if SWING_HORIZONTAL not in swing_modes:
            return None, None
        if val == SWING_OFF:
            if current_swing_mode == SWING_BOTH or current_swing_mode == SWING_VERTICAL:
                h_attributes[ATTR_SWING_MODE] = SWING_VERTICAL
            else:
                h_attributes[ATTR_SWING_MODE] = SWING_OFF
        else:
            if current_swing_mode == SWING_BOTH or current_swing_mode == SWING_VERTICAL:
                h_attributes[ATTR_SWING_MODE] = SWING_BOTH
            else:
                h_attributes[ATTR_SWING_MODE] = SWING_HORIZONTAL
        return service, h_attributes

    def h2v_current_temperature(self, device_id: str, index: int, on_off: dict, val):
        try:
            unit = Utils.get_entity_unit(self.hass, device_id)
            VLog.info(
                _TAG, f"[h2v_current_temperature] {device_id}  unit={unit} val:{val}"
            )
            if unit == "°F":
                VLog.info(_TAG, f"temperature unit is {unit} need to cover °C")
                return int(round((val - 32) * 5 / 9))
            if unit == "K":
                VLog.info(_TAG, f"temperature unit is {unit} need to cover °C")
                return int(round(val - 273.15))
            return int(round(float(val)))
        except ValueError as e:
            VLog.info(_TAG, f"[h2v_current_temperature] val format error:{val} {e}")
            return None

    def h2v_current_humidity(self, device_id: str, index: int, on_off: dict, val):
        VLog.info(_TAG, f"[h2v_current_humidity] val:{val}")
        try:
            return int(round(float(val)))
        except ValueError as e:
            VLog.info(_TAG, f"[h2v_current_humidity] val format error:{val} {e}")
            return None

    @classmethod
    def model_get(cls, hass: HomeAssistant,entity_id: str, entity_attributes: Mapping[str, Any]) -> list:
        model: list = []
        supported_features = entity_attributes.get(ATTR_SUPPORTED_FEATURES, 0)
        VLog.info(_TAG,
                  f"[model_get] ClimateEntityFeature(self.supported_features)={ClimateEntityFeature(supported_features)}"
                  f"\n entity_attributes = {entity_attributes}")
        _power_mode = VAttributeUtils.get_model_item(Platform.CLIMATE, "power")
        if _power_mode is not None:
            model.append(_power_mode)
        if (ClimateEntityFeature.TARGET_TEMPERATURE & ClimateEntityFeature(supported_features)) != 0:
            # 支持设置目标温度
            h_key = "target_temperature"
            VLog.info(_TAG, f"[model_get] {entity_id} support {h_key}")
            _target_temperature_model = VAttributeUtils.get_model_item(Platform.CLIMATE, h_key)
            if _target_temperature_model is not None:
                unit = Utils.get_entity_unit(hass, entity_id)
                _min_temp = entity_attributes.get(ATTR_MIN_TEMP, CLIMATE_MIN_TEMP)
                _max_temp = entity_attributes.get(ATTR_MAX_TEMP, CLIMATE_MAX_TEMP)
                if unit == "°F":
                    VLog.info(_TAG, f"temperature unit is {unit} need to cover °C")
                    _min_temp = int(round((_min_temp - 32) * 5 / 9))
                    _max_temp = int(round((_max_temp - 32) * 5 / 9))
                if unit == "K":
                    VLog.info(_TAG, f"temperature unit is {unit} need to cover °C")
                    _min_temp =  int(round(_min_temp - 273.15))
                    _max_temp =  int(round(_max_temp - 273.15))

                _climate_step = entity_attributes.get(
                    ATTR_TARGET_TEMP_STEP, CLIMATE_TEMP_STEP
                )
                _target_temperature_model["value_range"] = [
                    _min_temp,
                    _max_temp,
                    _climate_step,
                ]
                if _climate_step is not None:
                    model.append(_target_temperature_model)
        if (ClimateEntityFeature.TARGET_HUMIDITY & ClimateEntityFeature(supported_features)) != 0:
            # 支持室内湿度
            h_key = "current_humidity"
            VLog.info(_TAG, f"[model_get] {entity_id} support {h_key}")
            _current_humidity_model = VAttributeUtils.get_model_item(Platform.CLIMATE, h_key)
            if _current_humidity_model is not None:
                _min_humidity = entity_attributes.get(ATTR_MIN_HUMIDITY, CLIMATE_MIN_HUMIDITY)
                _max_humidity = entity_attributes.get(ATTR_MAX_HUMIDITY, CLIMATE_MAX_HUMIDITY)
                _current_humidity_model["value_range"] = [_min_humidity, _max_humidity, CLIMATE_HUMIDITY_STEP]
                model.append(_current_humidity_model)
        if (ClimateEntityFeature.FAN_MODE & ClimateEntityFeature(supported_features)) != 0:
            # 支持设置风扇模式
            h_fan_modes: list = entity_attributes.get(ATTR_FAN_MODES, None)
            if h_fan_modes is not None and len(h_fan_modes) > 0:
                h_key = ATTR_FAN_MODES
                v_fan_mode_dict: dict = VAttributeUtils.get_model_item(Platform.CLIMATE, h_key)
                if v_fan_mode_dict is not None:
                    v_fan_mode_dict["value_list"] = VAttributeUtils.get_value_list(v_fan_mode_dict["value_list"],
                                                                                   h_fan_modes, [])
                    if v_fan_mode_dict["value_list"] is not None and len(v_fan_mode_dict["value_list"]) > 0:
                        VLog.info(_TAG, f"[model_get] {entity_id} "
                                        f"support {h_key}:{v_fan_mode_dict["value_list"]} fan_modes:{h_fan_modes}")
                        model.append(v_fan_mode_dict)
        if (ClimateEntityFeature.SWING_MODE & ClimateEntityFeature(supported_features)) != 0:
            h_key = "swing_modes"
            swing_modes: list = entity_attributes.get(h_key)
            if SWING_VERTICAL in swing_modes:
                h_key_swing_modes_vertical = VIVO_CLIMATE_SWING_MODE_VERTICAL_H_NAME
                temp_mode: dict = VAttributeUtils.get_model_item(Platform.CLIMATE, h_key_swing_modes_vertical)
                if temp_mode is not None:
                    temp_mode["value_list"] = VAttributeUtils.get_support_value_list(temp_mode["value_list"],
                                                                                     swing_modes)
                    if temp_mode["value_list"] is not None and len(temp_mode["value_list"]) > 0:
                        model.append(temp_mode)
            if SWING_HORIZONTAL in swing_modes:
                h_key_swing_modes_horizontal = VIVO_CLIMATE_SWING_MODE_HORIZONTAL_H_NAME
                temp_mode: dict = VAttributeUtils.get_model_item(Platform.CLIMATE, h_key_swing_modes_horizontal)
                if temp_mode is not None:
                    temp_mode["value_list"] = VAttributeUtils.get_support_value_list(temp_mode["value_list"],
                                                                                     swing_modes)
                    if temp_mode["value_list"] is not None and len(temp_mode["value_list"]) > 0:
                        model.append(temp_mode)
        current_temperature = entity_attributes.get("current_temperature", None)
        if current_temperature is not None:
            h_key = "current_temperature"
            VLog.info(_TAG, f"[model_get] {entity_id} support {h_key}")
            _current_temperature_model = VAttributeUtils.get_model_item(Platform.CLIMATE, h_key)
            if _current_temperature_model is not None:
                model.append(VAttributeUtils.get_model_item(Platform.CLIMATE, h_key))

        h_hvac_modes: list = entity_attributes.get(ATTR_HVAC_MODES, None)
        if h_hvac_modes is not None and len(h_hvac_modes) > 0:
            h_key = ATTR_HVAC_MODES
            v_hvac_mode_dict: dict = VAttributeUtils.get_model_item(Platform.CLIMATE, h_key)
            if v_hvac_mode_dict is not None:
                v_hvac_mode_dict["value_list"] = VAttributeUtils.get_value_list(v_hvac_mode_dict["value_list"],
                                                                                h_hvac_modes, ["off"])
                if v_hvac_mode_dict["value_list"] is not None and len(v_hvac_mode_dict["value_list"]) > 0:
                    VLog.info(_TAG, f"[model_get] {entity_id} support "
                                    f"{h_key}:{v_hvac_mode_dict["value_list"]} hvac_modes:{h_hvac_modes}")
                    model.append(v_hvac_mode_dict)
        return model

    @classmethod
    def calibrate_current_attrs(cls, h_attributes: dict, new_state: str, old_state: str):
        if ATTR_SWING_MODE in h_attributes:
            if h_attributes[ATTR_SWING_MODE] is None:
                h_attributes[VIVO_CLIMATE_SWING_MODE_VERTICAL_H_NAME] = "off"
                h_attributes[VIVO_CLIMATE_SWING_MODE_HORIZONTAL_H_NAME] = "off"
            elif h_attributes[ATTR_SWING_MODE] == SWING_HORIZONTAL:
                h_attributes[VIVO_CLIMATE_SWING_MODE_HORIZONTAL_H_NAME] = SWING_HORIZONTAL
            elif h_attributes[ATTR_SWING_MODE] == SWING_VERTICAL:
                h_attributes[VIVO_CLIMATE_SWING_MODE_VERTICAL_H_NAME] = SWING_VERTICAL
            elif h_attributes[ATTR_SWING_MODE] == SWING_BOTH:
                h_attributes[VIVO_CLIMATE_SWING_MODE_VERTICAL_H_NAME] = SWING_VERTICAL
                h_attributes[VIVO_CLIMATE_SWING_MODE_HORIZONTAL_H_NAME] = SWING_HORIZONTAL
            else:
                VLog.info(_TAG, f"[calibrate_current_attrs] not support {h_attributes}")
        if new_state != old_state:
            h_attributes[ATTR_HVAC_ACTION] = new_state

    @classmethod
    def calibrate_swing_mode_attr_when_flush(cls, h_attributes: dict):
        if ATTR_SWING_MODE in h_attributes:
            if h_attributes[ATTR_SWING_MODE] == SWING_HORIZONTAL:
                h_attributes[VIVO_CLIMATE_SWING_MODE_HORIZONTAL_H_NAME] = SWING_HORIZONTAL
            elif h_attributes[ATTR_SWING_MODE] == SWING_VERTICAL:
                h_attributes[VIVO_CLIMATE_SWING_MODE_VERTICAL_H_NAME] = SWING_VERTICAL
            elif h_attributes[ATTR_SWING_MODE] == SWING_BOTH:
                h_attributes[VIVO_CLIMATE_SWING_MODE_VERTICAL_H_NAME] = SWING_VERTICAL
                h_attributes[VIVO_CLIMATE_SWING_MODE_HORIZONTAL_H_NAME] = SWING_HORIZONTAL
            else:
                VLog.info(_TAG, f"[calibrate_current_attrs_when_flush] no convert for {h_attributes}")