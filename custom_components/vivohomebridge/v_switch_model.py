"""
Copyright 2024 vivo Mobile Communication Co., Ltd.
Licensed under the Apache License, Version 2.0 (the "License");

   http://www.apache.org/licenses/LICENSE-2.0
"""

from typing import Mapping, Any

from .v_attribute import VIVO_KEY_WORD_V_NAME, VIVO_KEY_WORD_H_NAME
from .v_utils.vattributes_utils import VAttributeUtils
from .v_utils.vlog import VLog
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.components.switch import (
    SwitchDeviceClass,
    SERVICE_TURN_ON,
    SERVICE_TURN_OFF,
)
from .const import (
    VIVO_HA_PLATFORM_SOCKET_PK,
    VIVO_HA_PLATFORM_SWITCH_PK,
)

_TAG = "switch"

VIVO_HA_SWITCH_PK: dict = {
    SwitchDeviceClass.OUTLET: VIVO_HA_PLATFORM_SOCKET_PK,
    SwitchDeviceClass.SWITCH: VIVO_HA_PLATFORM_SWITCH_PK,
}


class VSwitchModel:
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, domain: str) -> None:
        self.hass = hass
        self.entry = entry
        self.domain = domain
        self.attributes_map = [
            {
                VIVO_KEY_WORD_V_NAME: "vivo_std_power",
                VIVO_KEY_WORD_H_NAME: "power",
                "v2h_converter": self.v2h_onoff,
                "h2v_converter": self.h2v_onoff,
            }
        ]

    def v2h_onoff(self, device_id: str, index: int, on_off: dict, val):
        """Turn off the climate."""
        VLog.info(_TAG, f"[v2h_onoff],val:{val}")
        service: str = SERVICE_TURN_ON
        h_attributes: dict = {"entity_id": device_id}
        if val == "off":
            service = SERVICE_TURN_OFF
        else:
            service = SERVICE_TURN_ON
        return service, h_attributes

    def h2v_onoff(self, device_id: str, index: int, on_off: dict, val):
        VLog.info(_TAG, f"[h2v_onoff] {device_id} {index}: {val}")
        if val == "off":
            return "off"
        return "on"

    @classmethod
    def model_get(cls,hass: HomeAssistant, entity_id: str, entity_attributes: Mapping[str, Any]) -> list:
        VLog.info(
            _TAG, f"[model_get]{entity_id},entity_attributes = {entity_attributes}"
        )
        model: list = [VAttributeUtils.get_model_item(Platform.SWITCH, "power")]
        return model
