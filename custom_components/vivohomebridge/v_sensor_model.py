"""
 Copyright 2024 vivo Mobile Communication Co., Ltd.
 Licensed under the Apache License, Version 2.0 (the "License");

    http://www.apache.org/licenses/LICENSE-2.0
"""
from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_DEVICE_CLASS,CONF_UNIT_OF_MEASUREMENT, Platform
from homeassistant.core import HomeAssistant
from .const import (VIVO_HA_PLATFORM_COMMON_SENSOR_PK, 
                    VIVO_HA_PLATFORM_HUMIDITY_TEMPERATURE_PK, 
                    VIVO_HA_PLATFORM_ILLUMINANCE_PK, 
                    VIVO_HA_PLATFORM_OCCUPANCY_PK, 
                    VIVO_HA_PLATFORM_OPENING_PK,
                    VIVO_HA_PLATFORM_CO2_PK,
                    VIVO_HA_PLATFORM_CO_PK,
                    VIVO_HA_PLATFORM_PH_PK,
                    VIVO_HA_PLATFORM_PM1_PK,
                    VIVO_HA_PLATFORM_PM25_PK,
                    VIVO_HA_PLATFORM_PM4_PK,
                    VIVO_HA_PLATFORM_PM10_PK,
                    VIVO_HA_PLATFORM_POWER_PK,
                    VIVO_HA_PLATFORM_CURRENT_PK,
                    VIVO_HA_PLATFORM_VOLTAGE_PK,
                    VIVO_HA_PLATFORM_ENERGY_PK, 
                    VIVO_HA_PLATFORM_BATTERY_PK 
                    )
from .v_attribute import VIVO_KEY_WORD_V_NAME, VIVO_KEY_WORD_H_NAME,VIVO_KEY_WORK_SENSOR_CLASS
from .v_utils.vattributes_utils import VAttributeUtils
from .v_utils.vlog import VLog
_TAG = "sensor"

VIVO_HA_SENSORS_PK: dict = {
    SensorDeviceClass.ENUM: VIVO_HA_PLATFORM_COMMON_SENSOR_PK,
    SensorDeviceClass.HUMIDITY: VIVO_HA_PLATFORM_HUMIDITY_TEMPERATURE_PK,
    SensorDeviceClass.ILLUMINANCE: VIVO_HA_PLATFORM_ILLUMINANCE_PK,
    SensorDeviceClass.TEMPERATURE: VIVO_HA_PLATFORM_HUMIDITY_TEMPERATURE_PK,
    SensorDeviceClass.BATTERY: VIVO_HA_PLATFORM_BATTERY_PK,
    SensorDeviceClass.ENERGY: VIVO_HA_PLATFORM_ENERGY_PK,
    SensorDeviceClass.CURRENT: VIVO_HA_PLATFORM_CURRENT_PK,
    SensorDeviceClass.VOLTAGE: VIVO_HA_PLATFORM_VOLTAGE_PK,
    SensorDeviceClass.POWER: VIVO_HA_PLATFORM_POWER_PK,
    SensorDeviceClass.PM10: VIVO_HA_PLATFORM_PM10_PK,
    SensorDeviceClass.PM25: VIVO_HA_PLATFORM_PM25_PK,
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
                VIVO_KEY_WORK_SENSOR_CLASS: SensorDeviceClass.ENUM,
                VIVO_KEY_WORD_H_NAME:"state",
                # "v2h_converter": self.v2h_onoff,
                "h2v_converter": self.h2v_prop,
            },
            # 人体移动
            {
                VIVO_KEY_WORD_V_NAME: "vivo_std_person_move",
                VIVO_KEY_WORK_SENSOR_CLASS: BinarySensorDeviceClass.OCCUPANCY,
                VIVO_KEY_WORD_H_NAME:"state",
                # "v2h_converter": self.v2h_color_temp,
                "h2v_converter": self.h2v_person_move,
            },
            {
                VIVO_KEY_WORD_V_NAME: "vivo_std_person_move",
                VIVO_KEY_WORK_SENSOR_CLASS: BinarySensorDeviceClass.MOTION,
                VIVO_KEY_WORD_H_NAME:"state",
                # "v2h_converter": self.v2h_color_temp,
                "h2v_converter": self.h2v_person_move,
            },
            {
                VIVO_KEY_WORD_V_NAME: "vivo_std_person_move",
                VIVO_KEY_WORK_SENSOR_CLASS: BinarySensorDeviceClass.MOVING,
                VIVO_KEY_WORD_H_NAME:"state",
                # "v2h_converter": self.v2h_color_temp,
                "h2v_converter": self.h2v_person_move,
            },
            # 温度
            {
                VIVO_KEY_WORD_V_NAME: "vivo_std_temperature",
                VIVO_KEY_WORK_SENSOR_CLASS: SensorDeviceClass.TEMPERATURE,
                VIVO_KEY_WORD_H_NAME:"state",
                # "v2h_converter": self.v2h_brightness,
                "h2v_converter": self.h2v_prop,
            },
            # 湿度
            {
                VIVO_KEY_WORD_V_NAME: "vivo_std_humidity",
                VIVO_KEY_WORK_SENSOR_CLASS: SensorDeviceClass.HUMIDITY,
                VIVO_KEY_WORD_H_NAME:"state",
                # "v2h_converter": self.v2h_color_rgb,
                "h2v_converter": self.h2v_prop,
            },
            # 电量
            {
                VIVO_KEY_WORD_V_NAME: "vivo_std_battery",
                VIVO_KEY_WORK_SENSOR_CLASS: SensorDeviceClass.BATTERY,
                VIVO_KEY_WORD_H_NAME:"state",
                # "v2h_converter": self.v2h_color_temp,
                "h2v_converter": self.h2v_prop,
            },
            # 光照
            {
                VIVO_KEY_WORD_V_NAME: "vivo_std_illuminance",
                VIVO_KEY_WORK_SENSOR_CLASS: SensorDeviceClass.ILLUMINANCE,
                VIVO_KEY_WORD_H_NAME:"state",
                # "v2h_converter": self.v2h_color_temp,
                "h2v_converter": self.h2v_prop,
            },
            # 耗电量
            {
                
                VIVO_KEY_WORK_SENSOR_CLASS: SensorDeviceClass.ENERGY,
                "mWh":{
                    VIVO_KEY_WORD_V_NAME: "vivo_std_mWh",
                },
                "Wh":{
                    VIVO_KEY_WORD_V_NAME: "vivo_std_Wh",
                },
                "kWh":{
                    VIVO_KEY_WORD_V_NAME: "vivo_std_kWh",
                },
                "MWh":{
                    VIVO_KEY_WORD_V_NAME: "vivo_std_M_Wh",
                },
                "GWh":{
                    VIVO_KEY_WORD_V_NAME: "vivo_std_GWh",
                },
                "TWh":{
                    VIVO_KEY_WORD_V_NAME: "vivo_std_TWh",
                },
                VIVO_KEY_WORD_H_NAME:"state",
                "h2v_converter": self.h2v_prop,
            },
            # 电功率
            {
                VIVO_KEY_WORK_SENSOR_CLASS: SensorDeviceClass.POWER,
                "mW":{
                    VIVO_KEY_WORD_V_NAME: "vivo_std_mW",
                },
                "W":{
                    VIVO_KEY_WORD_V_NAME: "vivo_std_W",
                },
                "kW":{
                    VIVO_KEY_WORD_V_NAME: "vivo_std_kW",
                },
                "MW":{
                    VIVO_KEY_WORD_V_NAME: "vivo_std_M_W",
                },
                "GW":{
                    VIVO_KEY_WORD_V_NAME: "vivo_std_GW",
                },
                "TW":{
                    VIVO_KEY_WORD_V_NAME: "vivo_std_TW",
                },
                VIVO_KEY_WORD_H_NAME:"state",
                "h2v_converter": self.h2v_prop,
            },
            # 电流
            {
                VIVO_KEY_WORK_SENSOR_CLASS: SensorDeviceClass.CURRENT,
                "mA":{
                    VIVO_KEY_WORD_V_NAME: "vivo_std_mA",
                },
                "A":{
                    VIVO_KEY_WORD_V_NAME: "vivo_std_A",
                },
                VIVO_KEY_WORD_H_NAME:"state",
                "h2v_converter": self.h2v_prop,
            },
            # 电压
            {
                VIVO_KEY_WORK_SENSOR_CLASS: SensorDeviceClass.VOLTAGE,
                "µV":{
                    VIVO_KEY_WORD_V_NAME: "vivo_std_µV",
                },
                "mV":{
                    VIVO_KEY_WORD_V_NAME: "vivo_std_mV",
                },
                "V":{
                    VIVO_KEY_WORD_V_NAME: "vivo_std_V",
                },
                "kV":{
                    VIVO_KEY_WORD_V_NAME: "vivo_std_kV",
                },
                VIVO_KEY_WORD_H_NAME:"state",
                "h2v_converter": self.h2v_prop,
            },
            # PM10
            {
                VIVO_KEY_WORD_V_NAME: "vivo_std_pm10",
                VIVO_KEY_WORK_SENSOR_CLASS: SensorDeviceClass.PM10,
                VIVO_KEY_WORD_H_NAME:"state",
                "h2v_converter": self.h2v_prop,
            },
            # PM2.5
            {
                VIVO_KEY_WORD_V_NAME: "vivo_std_pm25",
                VIVO_KEY_WORK_SENSOR_CLASS: SensorDeviceClass.PM25,
                VIVO_KEY_WORD_H_NAME:"state",
                "h2v_converter": self.h2v_prop,
            },
            {
                VIVO_KEY_WORD_V_NAME: "vivo_std_illuminance",
                VIVO_KEY_WORK_SENSOR_CLASS: BinarySensorDeviceClass.LIGHT,
                VIVO_KEY_WORD_H_NAME:"state",
                # "v2h_converter": self.v2h_color_temp,
                "h2v_converter": self.h2v_prop,
            },
            # 门磁
            {
                VIVO_KEY_WORD_V_NAME: "vivo_std_onoff",
                VIVO_KEY_WORK_SENSOR_CLASS: BinarySensorDeviceClass.DOOR,
                VIVO_KEY_WORD_H_NAME:"state",
                # "v2h_converter": self.v2h_color_temp,
                "h2v_converter": self.h2v_door,
            },
            {
                VIVO_KEY_WORD_V_NAME: "vivo_std_onoff",
                VIVO_KEY_WORK_SENSOR_CLASS: BinarySensorDeviceClass.GARAGE_DOOR,
                VIVO_KEY_WORD_H_NAME:"state",
                # "v2h_converter": self.v2h_color_temp,
                "h2v_converter": self.h2v_door,
            },
            {
                VIVO_KEY_WORD_V_NAME: "vivo_std_onoff",
                VIVO_KEY_WORK_SENSOR_CLASS: BinarySensorDeviceClass.OPENING,
                VIVO_KEY_WORD_H_NAME:"state",
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
        elif device_class == SensorDeviceClass.BATTERY:
            battery_model = VAttributeUtils.get_model_item(Platform.SENSOR, "battery")
            if battery_model:
                model.append(battery_model)
        elif device_class == SensorDeviceClass.ENERGY:
            unit = entity_attributes.get(CONF_UNIT_OF_MEASUREMENT)  
            VLog.info(_TAG, f"[model_get]energy unit:{unit}")
            energy_model = VAttributeUtils.get_model_item_by_unit(Platform.SENSOR, "energy", unit)
            if energy_model:
                model.append(energy_model)
        elif device_class == SensorDeviceClass.CURRENT:  
            unit = entity_attributes.get(CONF_UNIT_OF_MEASUREMENT)
            current_model = VAttributeUtils.get_model_item_by_unit(Platform.SENSOR, "current", unit)
            if current_model:
                model.append(current_model)
        elif device_class == SensorDeviceClass.VOLTAGE:
            unit = entity_attributes.get(CONF_UNIT_OF_MEASUREMENT)
            voltage_model = VAttributeUtils.get_model_item_by_unit(Platform.SENSOR, "voltage", unit)
            if voltage_model:
                model.append(voltage_model)
        elif device_class == SensorDeviceClass.POWER:
            unit = entity_attributes.get(CONF_UNIT_OF_MEASUREMENT)
            power_model = VAttributeUtils.get_model_item_by_unit(Platform.SENSOR, "power", unit)
            if power_model:
                model.append(power_model)
        elif device_class == SensorDeviceClass.PM10:
            pm10_model = VAttributeUtils.get_model_item(Platform.SENSOR, "pm10")
            if pm10_model:
                model.append(pm10_model)
        elif device_class == SensorDeviceClass.PM25:
            pm25_model = VAttributeUtils.get_model_item(Platform.SENSOR, "pm25")
            if pm25_model:
                model.append(pm25_model)
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
