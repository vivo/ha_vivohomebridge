"""
 Copyright 2024 vivo Mobile Communication Co., Ltd.
 Licensed under the Apache License, Version 2.0 (the "License");

    http://www.apache.org/licenses/LICENSE-2.0
"""
import copy
from enum import Enum

from homeassistant.const import ATTR_ENTITY_ID
from .vlog import VLog
from ..v_attribute import VIVO_KEY_WORD_V_NAME, VIVO_ATTR_NAME_POWER, VIVO_KEY_WORD_H_NAME,VIVO_KEY_WORK_SENSOR_CLASS,VIVO_KEY_WORD_NAME
from homeassistant.core import HomeAssistant
from ..v_attritube_map import v2h_attributes_map

_TAG = "attributes"


class VAttributeUtils:

    @staticmethod
    def h2v_attributes_converter(hass: HomeAssistant, entity_id: str, attributes_map: list, h_attributes: dict,
                                 skip_off_state: bool):
        v_data = {}

        if any(item[VIVO_KEY_WORD_V_NAME] == VIVO_ATTR_NAME_POWER for item in attributes_map):
            if hass.states.get(entity_id).state == 'unavailable':
                v_data[VIVO_ATTR_NAME_POWER] = 'off'
                return v_data
            elif hass.states.get(entity_id).state == 'off':
                v_data[VIVO_ATTR_NAME_POWER] = 'off'
                if skip_off_state is False:
                    return v_data
            else:
                v_data[VIVO_ATTR_NAME_POWER] = 'on'
        else:
            VLog.info(_TAG, f"{entity_id} had no {VIVO_ATTR_NAME_POWER} {attributes_map}")

        for key, val in h_attributes.items():
            if val is None:
                continue
            obj = next((item for item in attributes_map if item.get(VIVO_KEY_WORD_H_NAME) == key), None)
            if obj is None or obj['h2v_converter'] is None:
                continue
            h2v_converter = obj['h2v_converter']
            v_data[obj[VIVO_KEY_WORD_V_NAME]] = h2v_converter(entity_id, 0, obj, val)
        return v_data

    @staticmethod
    def v2h_attributes_converter(hass: HomeAssistant, h_device_id: str, entity_id: str, attributes_map: list,
                                 v_attributes: dict):
        h_data = {ATTR_ENTITY_ID: entity_id}
        for key, val in v_attributes.items():
            obj = next(
                (item for item in attributes_map if item.get(VIVO_KEY_WORD_V_NAME) == key), None)
            if obj:
                v2h_converter = obj['v2h_converter']
                if v2h_converter:
                    h_data[obj[VIVO_KEY_WORD_H_NAME]] = v2h_converter(
                        h_device_id, 0, obj, val)
        return h_data

    @staticmethod
    def get_model_item(platform: str, key: str):
        attributes_array = v2h_attributes_map[platform]
        new_item: dict = {}
        for item in attributes_array:
            # 复制原始字典，避免修改原始数据
            new_item = copy.deepcopy(item)
            if new_item[VIVO_KEY_WORD_H_NAME] == key:
                del new_item[VIVO_KEY_WORD_H_NAME]
                return new_item
        VLog.info(_TAG, f"[get_model_item] no attribute support for {platform},{key}")
        return None
    @staticmethod
    def get_model_item_by_unit(platform: str, key: str, unit: str):
        attributes_array = v2h_attributes_map.get(platform)
        if not isinstance(attributes_array, list):
            return None

        key_norm = key
        unit_norm = unit

        for item in attributes_array:
            if not isinstance(item, dict):
                continue
            h_name = item.get(VIVO_KEY_WORD_H_NAME)
            if h_name == key_norm:
                # 大小写敏感匹配单位
                for k, v in item.items():
                    if isinstance(k, str) and k == unit_norm and isinstance(v, dict):
                        return v
        return None

    

    @staticmethod
    def h2v_mode_get_value(platform: str, key: str, val):
        temp_mode: dict = VAttributeUtils.get_model_item(platform, key)
        if not temp_mode:
            return val
        value_list = temp_mode.get("value_list", [])
        if not value_list:
            return val
        v_value = next((item["value"] for item in value_list if item["h_value"] == val), None)
        if not v_value:
            return val
        else:
            return v_value

    @staticmethod
    def v2h_mode_get_attr(h_mode_key, h_attr_key, val, platform, h_attributes):
        temp_mode = VAttributeUtils.get_model_item(platform, h_mode_key)
        if not temp_mode:
            return h_attributes
        value_list = temp_mode.get("value_list", [])
        if not value_list:
            return h_attributes
        h_value = next((item["h_value"] for item in value_list if item["value"] == val), None)
        if not h_value:
            return h_attributes
        h_attributes[h_attr_key] = h_value
        return h_attributes

    @staticmethod
    def add_value_list_to_model(value_list: list) -> list:
        h_value_list: list = []
        if VAttributeUtils.is_list_of_enums(value_list):
            for value_item in value_list:
                h_value: dict = {"value": value_item.value, "description": value_item.value}
                h_value_list.append(h_value)
        else:
            for value_item in value_list:
                h_value: dict = {"value": value_item, "description": value_item}
                h_value_list.append(h_value)
        return h_value_list

    @staticmethod
    def is_list_of_enums(lst):
        return all(isinstance(item, Enum) for item in lst)

    @staticmethod
    def get_support_value_list(v_o_values: list, h_o_values: list) -> list:
        value_list: list = []
        v_values = copy.deepcopy(v_o_values)
        for v_value_item in v_values:
            h_value = v_value_item.get("h_value")
            if h_value and h_value in h_o_values:
                del v_value_item["h_value"]
                value_list.append(v_value_item)
        return value_list

    @staticmethod
    def get_value_list(v_o_values: list, h_o_values: list, ignore_list: list) -> list:
        """ ha 匹配 vivo
        例如 ha: [A,B,C,D]; vivo [B,C,E] => [A,B,C,D]
        """
        value_list: list = []
        if VAttributeUtils.is_list_of_enums(h_o_values):
            for h_enum_item in h_o_values:
                if h_enum_item.value in ignore_list:
                    continue
                found = False
                for v_item in v_o_values:
                    if h_enum_item.value == v_item.get("h_value"):
                        value_list.append({"value": v_item["value"], "description": v_item["description"]})
                        found = True
                        break
                if not found:
                    value_list.append({"value": h_enum_item.value, "description": h_enum_item.value})
        else:
            for h_item in h_o_values:
                if h_item in ignore_list:
                    continue
                found = False
                for v_item in v_o_values:
                    if h_item == v_item.get("h_value"):
                        value_list.append({"value": v_item["value"], "description": v_item["description"]})
                        found = True
                        break
                if not found:
                    value_list.append({"value": h_item, "description": h_item})
        return value_list

    @staticmethod
    def flatten_multi_unit_item_case_sensitive(item: dict, unit: str):
        """
            return:
            {
                VIVO_KEY_WORD_V_NAME: "vivo_std_kWh",
                VIVO_KEY_WORK_SENSOR_CLASS: SensorDeviceClass.ENERGY,
                VIVO_KEY_WORD_H_NAME: "state",
                "h2v_converter": self.h2v_prop,
            }
        """
        # 基本类型与参数校验
        if not isinstance(item, dict) or not isinstance(unit, str):
            return None

        # 精确匹配单位键（大小写敏感）
        sub = item.get(unit)
        if not isinstance(sub, dict):
            # 未找到对应单位或结构不正确
            return None

        v_name = sub.get(VIVO_KEY_WORD_V_NAME)
        if not isinstance(v_name, str):
            return None

        # 构造结果：合并公共字段 + 该单位的 VIVO_KEY_WORD_V_NAME
        result = {
            VIVO_KEY_WORD_V_NAME: v_name,
        }

        # 复制公共字段（仅复制这些键，避免把其他单位键带进来）
        for k in (VIVO_KEY_WORK_SENSOR_CLASS, VIVO_KEY_WORD_H_NAME, "h2v_converter", "v2h_converter"):
            if k in item:
                result[k] = item[k]

        return result