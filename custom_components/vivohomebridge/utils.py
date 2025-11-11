"""
 Copyright 2024 vivo Mobile Communication Co., Ltd.
 Licensed under the Apache License, Version 2.0 (the "License");

    http://www.apache.org/licenses/LICENSE-2.0
"""

from homeassistant.const import CONF_UNIT_OF_MEASUREMENT
from homeassistant.helpers import entity_registry as er
from .const import VIVO_HA_KEY_WORLD_DEV_LOGIC_MAC, VIVO_DEVICE_NAME_CONFIG_KEY, \
    VIVO_DEVICE_ENTITY_ID_KEY, VIVO_HA_KEY_WORLD_DEV_ENTRY_ID, VIVO_DEVICE_NAME_FRIENDLY_KEY,VIVO_DEVICE_ID_KEY


class Utils:

    @staticmethod
    def get_entity_id_by_name(dname: str, bridge_config_data: list):
        obj = next(
            (item for item in bridge_config_data if item.get(VIVO_DEVICE_NAME_CONFIG_KEY, None) == dname), None)
        if obj:
            return obj[VIVO_DEVICE_ENTITY_ID_KEY]
        return None

    @staticmethod
    def get_entry_id_from_entity_id(entity_id: str, bridge_config_data: list):
        obj = next(
            (item for item in bridge_config_data if item.get(VIVO_DEVICE_ENTITY_ID_KEY, None) == entity_id), None)
        if obj:
            return obj.get(VIVO_HA_KEY_WORLD_DEV_ENTRY_ID, None)
        return None

    @staticmethod
    def get_entity_id_by_logic_mac(logic_mac: str, bridge_config_data: list):
        obj = next(
            (item for item in bridge_config_data if item.get(VIVO_HA_KEY_WORLD_DEV_LOGIC_MAC, None) == logic_mac), None)
        if obj:
            return obj[VIVO_DEVICE_ENTITY_ID_KEY]
        return None

    @staticmethod 
    def get_logic_mac_by_entity_id( entry_id: str, bridge_config_data: list ):
        obj = next(
            (item for item in bridge_config_data if item.get(VIVO_DEVICE_ENTITY_ID_KEY, None) == entry_id), None)
        if obj:
            return obj[VIVO_HA_KEY_WORLD_DEV_LOGIC_MAC]
        return None
        
    @staticmethod
    def get_entity_ids_from_entry_id(entry_id: str, bridge_config_data: list):
        return [item[VIVO_DEVICE_ENTITY_ID_KEY] for item in bridge_config_data
                if item.get(VIVO_HA_KEY_WORLD_DEV_ENTRY_ID, None) == entry_id]

    @staticmethod
    def get_entity_ids(bridge_config_data: list):
        return [item[VIVO_DEVICE_ENTITY_ID_KEY] for item in bridge_config_data]

    @staticmethod
    def get_device_id_by_name(dname: str, bridge_config_data: list):
        obj = next(
            (item for item in bridge_config_data if item.get(VIVO_DEVICE_NAME_CONFIG_KEY, None) == dname), None)
        if obj:
            return obj[VIVO_DEVICE_ID_KEY]
        return None

    @staticmethod
    async def get_entity_id_from_registry_id(hass, registry_id: str) -> str | None:
        entity_registry = er.async_get(hass)
        for entity in entity_registry.entities.values():
            if entity.id == registry_id:
                return entity.entity_id
        return None
    
    @staticmethod
    async def get_device_id_from_entity_id(hass, entity_id):
        # 获取实体注册表
        entity_registry = er.async_get(hass)
        
        # 通过entity_id获取实体注册信息
        entity_entry = entity_registry.async_get(entity_id)
        
        if entity_entry is None:
            return None
        
        # 从实体信息中获取device_id
        return entity_entry.device_id

    @staticmethod
    def get_entity_unit(hass, entity_id):
        state = hass.states.get(entity_id)
        if state:
            unit = state.attributes.get(CONF_UNIT_OF_MEASUREMENT)
            if unit is None:
                sys_temperature_unit = hass.config.units.temperature_unit
                return sys_temperature_unit
            return unit
        return None
    def get_device_id(entity_id: str, bridge_config_data: list):
        obj = next((item for item in bridge_config_data if item.get(VIVO_DEVICE_ENTITY_ID_KEY, None) == entity_id), None)
        if obj:
            return obj[VIVO_DEVICE_ID_KEY]
        return None

    @staticmethod
    def get_dn(entity_id: str, bridge_config_data: list):
        obj = next((item for item in bridge_config_data if item.get(VIVO_DEVICE_ENTITY_ID_KEY, None) == entity_id), None)
        if obj:
            return obj[VIVO_DEVICE_NAME_CONFIG_KEY]
        return None

    @staticmethod
    def get_fn(entity_id: str, bridge_config_data: list):
        obj = next((item for item in bridge_config_data if item.get(VIVO_DEVICE_ENTITY_ID_KEY, None) == entity_id),
                   None)
        if obj:
            return obj[VIVO_DEVICE_NAME_FRIENDLY_KEY]
        return None

    @staticmethod
    def get_cpuinfo_model():
        try:
            with open("/proc/cpuinfo", "r") as f:
                for line in f:
                    if line.startswith("Model"):
                        return line.split(":")[1].strip()
        except Exception as e:
            return "Unknown"
