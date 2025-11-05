"""
 Copyright 2024 vivo Mobile Communication Co., Ltd.
 Licensed under the Apache License, Version 2.0 (the "License");

    http://www.apache.org/licenses/LICENSE-2.0
"""
from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_DEVICE_CLASS, Platform
from homeassistant.core import HomeAssistant
from .const import VIVO_HA_PLATFORM_COMMON_SENSOR_PK, VIVO_HA_PLATFORM_HUMIDITY_TEMPERATURE_PK, \
    VIVO_HA_PLATFORM_ILLUMINANCE_PK, VIVO_HA_PLATFORM_OCCUPANCY_PK, VIVO_HA_PLATFORM_OPENING_PK
from .v_attribute import VIVO_KEY_WORD_V_NAME, VIVO_KEY_WORD_H_NAME
from .v_utils.vattributes_utils import VAttributeUtils
from .v_utils.vlog import VLog
_TAG = "sensor"

VIVO_HA_SENSORS_PK: dict = {
    SensorDeviceClass.ENUM: VIVO_HA_PLATFORM_COMMON_SENSOR_PK,
    SensorDeviceClass.HUMIDITY: VIVO_HA_PLATFORM_HUMIDITY_TEMPERATURE_PK,
    SensorDeviceClass.ILLUMINANCE: VIVO_HA_PLATFORM_ILLUMINANCE_PK,
    SensorDeviceClass.TEMPERATURE: VIVO_HA_PLATFORM_HUMIDITY_TEMPERATURE_PK,
    BinarySensorDeviceClass.OCCUPANCY: VIVO_HA_PLATFORM_OCCUPANCY_PK,
    BinarySensorDeviceClass.DOOR: VIVO_HA_PLATFORM_OPENING_PK,
    BinarySensorDeviceClass.GARAGE_DOOR: VIVO_HA_PLATFORM_OPENING_PK,
    BinarySensorDeviceClass.OPENING: VIVO_HA_PLATFORM_OPENING_PK,
    BinarySensorDeviceClass.MOTION: VIVO_HA_PLATFORM_OCCUPANCY_PK,
    BinarySensorDeviceClass.MOVING: VIVO_HA_PLATFORM_OCCUPANCY_PK,
}


class VSensorModel:
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, domain: str) -> None:
        self.hass = hass
        self.entry = entry
        self.domain = domain
        self.attributes_map = [
            # 通用
            {
                VIVO_KEY_WORD_V_NAME: "vivo_std_sensor_value",
                VIVO_KEY_WORD_H_NAME: SensorDeviceClass.ENUM,
                # "v2h_converter": self.v2h_onoff,
                "h2v_converter": self.h2v_prop,
            },
            # 人体移动
            {
                VIVO_KEY_WORD_V_NAME: "vivo_std_person_move",
                VIVO_KEY_WORD_H_NAME: BinarySensorDeviceClass.OCCUPANCY,
                # "v2h_converter": self.v2h_color_temp,
                "h2v_converter": self.h2v_person_move,
            },
            {
                VIVO_KEY_WORD_V_NAME: "vivo_std_person_move",
                VIVO_KEY_WORD_H_NAME: BinarySensorDeviceClass.MOTION,
                # "v2h_converter": self.v2h_color_temp,
                "h2v_converter": self.h2v_person_move,
            },
            {
                VIVO_KEY_WORD_V_NAME: "vivo_std_person_move",
                VIVO_KEY_WORD_H_NAME: BinarySensorDeviceClass.MOVING,
                # "v2h_converter": self.v2h_color_temp,
                "h2v_converter": self.h2v_person_move,
            },
            # 温度
            {
                VIVO_KEY_WORD_V_NAME: "vivo_std_temperature",
                VIVO_KEY_WORD_H_NAME: SensorDeviceClass.TEMPERATURE,
                # "v2h_converter": self.v2h_brightness,
                "h2v_converter": self.h2v_prop,
            },
            # # 湿度
            {
                VIVO_KEY_WORD_V_NAME: "vivo_std_humidity",
                VIVO_KEY_WORD_H_NAME: SensorDeviceClass.HUMIDITY,
                # "v2h_converter": self.v2h_color_rgb,
                "h2v_converter": self.h2v_prop,
            },
            # 电量
            {
                VIVO_KEY_WORD_V_NAME: "vivo_std_battery",
                VIVO_KEY_WORD_H_NAME: SensorDeviceClass.BATTERY,
                # "v2h_converter": self.v2h_color_temp,
                "h2v_converter": self.h2v_prop,
            },
            # 光照
            {
                VIVO_KEY_WORD_V_NAME: "vivo_std_illuminance",
                VIVO_KEY_WORD_H_NAME: SensorDeviceClass.ILLUMINANCE,
                # "v2h_converter": self.v2h_color_temp,
                "h2v_converter": self.h2v_prop,
            },
            {
                VIVO_KEY_WORD_V_NAME: "vivo_std_illuminance",
                VIVO_KEY_WORD_H_NAME: BinarySensorDeviceClass.LIGHT,
                # "v2h_converter": self.v2h_color_temp,
                "h2v_converter": self.h2v_prop,
            },
            # # 门磁
            {
                VIVO_KEY_WORD_V_NAME: "vivo_std_onoff",
                VIVO_KEY_WORD_H_NAME: BinarySensorDeviceClass.DOOR,
                # "v2h_converter": self.v2h_color_temp,
                "h2v_converter": self.h2v_door,
            },
            {
                VIVO_KEY_WORD_V_NAME: "vivo_std_onoff",
                VIVO_KEY_WORD_H_NAME: BinarySensorDeviceClass.GARAGE_DOOR,
                # "v2h_converter": self.v2h_color_temp,
                "h2v_converter": self.h2v_door,
            },
            {
                VIVO_KEY_WORD_V_NAME: "vivo_std_onoff",
                VIVO_KEY_WORD_H_NAME: BinarySensorDeviceClass.OPENING,
                # "v2h_converter": self.v2h_color_temp,
                "h2v_converter": self.h2v_door,
            },
        ]

    def h2v_person_move(self, device_id: str, index: int, attributes_map_item: dict, val):
        VLog.info(_TAG, f"[h2v_person_move]{val}")
        # Convert "on"/"off" to True/False
        if val in ["on", "off"]:
            return val == "on"
        return val

    def h2v_door(self, device_id: str, index: int, attributes_map_item: dict, val):
        VLog.info(_TAG, f"[h2v_door]{val}")
        return val

    def h2v_prop(self, device_id: str, index: int, attributes_map_item: dict, val):
        VLog.info(_TAG, f"[h2v_prop]{val}")
        return val

    @staticmethod
    def sensor_h2v_val(device_class: str, unit: str, val):
        VLog.info(_TAG, f"[sensor_h2v_val]{val}")
        if val == "unavailable":
            return ""
        if device_class == SensorDeviceClass.TEMPERATURE:
            try:
                val_num = float(val)
            except ValueError:
                VLog.error(_TAG, f"温度传感器值类型转换异常，原始值：{val}")
                return 0.0
            if unit == "°F":
                return f"{((val_num - 32) * 5 / 9):.1f}"
            elif unit == "K":
                return f"{(val_num - 273.15):.1f}"
            else:
                return val
        else:
            return val

    @classmethod
    def model_get(cls, hass: HomeAssistant, entity_id, entity_attributes):
        VLog.info(_TAG, f"[model_get]sensor_model_get:{entity_attributes.get(ATTR_DEVICE_CLASS)}")
        model: list = []
        device_class = entity_attributes.get(ATTR_DEVICE_CLASS)
        current_battery_model = VAttributeUtils.get_model_item(Platform.SENSOR, "current_battery")
        if current_battery_model:
            model.append(current_battery_model)
        if device_class == SensorDeviceClass.TEMPERATURE:
            current_temperature_model = VAttributeUtils.get_model_item(Platform.SENSOR, "current_temperature")
            if current_temperature_model:
                model.append(current_temperature_model)
        elif device_class == SensorDeviceClass.HUMIDITY:
            current_humidity_model = VAttributeUtils.get_model_item(Platform.SENSOR, "current_humidity")
            if current_humidity_model:
                model.append(current_humidity_model)
        elif device_class == SensorDeviceClass.ENUM:
            sensor_value_model = VAttributeUtils.get_model_item(Platform.SENSOR, "sensor_value")
            if sensor_value_model:
                model.append(sensor_value_model)
        elif device_class == SensorDeviceClass.ILLUMINANCE:
            illuminance_model = VAttributeUtils.get_model_item(Platform.SENSOR, "illuminance")
            if illuminance_model:
                model.append(illuminance_model)
        elif (device_class == BinarySensorDeviceClass.OCCUPANCY or device_class == BinarySensorDeviceClass.MOTION
                or device_class == BinarySensorDeviceClass.MOVING):
            move_model = VAttributeUtils.get_model_item(Platform.SENSOR, "move")
            if move_model:
                model.append(move_model)
        elif (device_class == BinarySensorDeviceClass.DOOR or device_class == BinarySensorDeviceClass.GARAGE_DOOR
                or device_class == BinarySensorDeviceClass.OPENING):
            power_model = VAttributeUtils.get_model_item(Platform.SENSOR, "power")
            if power_model:
                model.append(power_model)
        return model
