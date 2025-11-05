"""
 Copyright 2024 vivo Mobile Communication Co., Ltd.
 Licensed under the Apache License, Version 2.0 (the "License");

    http://www.apache.org/licenses/LICENSE-2.0
"""
from typing import Mapping, Any
from homeassistant.const import ATTR_ENTITY_ID, ATTR_SUPPORTED_FEATURES, Platform
from .v_attribute import VIVO_KEY_WORD_V_NAME, VIVO_KEY_WORD_H_NAME
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .v_utils.vattributes_utils import VAttributeUtils
from .v_utils.vlog import VLog
from homeassistant.components.cover import (
    SERVICE_CLOSE_COVER,
    SERVICE_OPEN_COVER,
    SERVICE_SET_COVER_POSITION,
    SERVICE_STOP_COVER,
    ATTR_POSITION, CoverEntityFeature
)
_TAG = "cover"


class VCoverModel:
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, domain: str) -> None:
        self.hass = hass
        self.entry = entry
        self.domain = domain
        self.attributes_map = [
            {
                VIVO_KEY_WORD_V_NAME: "vivo_std_window_covering",
                VIVO_KEY_WORD_H_NAME: "current_position",
                "v2h_converter": self.v2h_set_position,
                "h2v_converter": self.h2v_set_position,
            }, {
                VIVO_KEY_WORD_V_NAME: "vivo_std_window_open",
                VIVO_KEY_WORD_H_NAME: "open",
                "v2h_converter": self.v2h_open,
                "h2v_converter": None,
            }, {
                VIVO_KEY_WORD_V_NAME: "vivo_std_window_close",
                VIVO_KEY_WORD_H_NAME: "close",
                "v2h_converter": self.v2h_close,
                "h2v_converter": None,
            }, {
                VIVO_KEY_WORD_V_NAME: "vivo_std_window_pause",
                VIVO_KEY_WORD_H_NAME: "stop",
                "v2h_converter": self.v2h_stop,
                "h2v_converter": None,
            }
        ]

    def v2h_set_position(self, entity_id: str, index: int, on_off: dict, val):
        service: str = SERVICE_SET_COVER_POSITION
        h_attributes: dict = {}
        VLog.info(_TAG, f"[v2h_set_position],val:{val}")
        h_attributes[ATTR_ENTITY_ID] = entity_id
        h_attributes[ATTR_POSITION] = val
        return service, h_attributes

    def h2v_set_position(self, entity_id: str, index: int, on_off: dict, val):
        VLog.info(_TAG, f"[h2v_set_position],val:{val}")
        return val

    def v2h_open(self, entity_id: str, index: int, on_off: dict, val):
        service: str = SERVICE_OPEN_COVER
        h_attributes: dict = {}
        VLog.info(_TAG, f"[v2h_open],val:{val}")
        h_attributes[ATTR_ENTITY_ID] = entity_id
        return service, h_attributes

    def v2h_close(self, entity_id: str, index: int, on_off: dict, val):
        service: str = SERVICE_CLOSE_COVER
        h_attributes: dict = {}
        VLog.info(_TAG, f"[v2h_close],val:{val}")
        h_attributes[ATTR_ENTITY_ID] = entity_id
        return service, h_attributes

    def v2h_stop(self, entity_id: str, index: int, on_off: dict, val):
        service: str = SERVICE_STOP_COVER
        h_attributes: dict = {}
        VLog.info(_TAG, f"[v2h_stop],val:{val}")
        h_attributes[ATTR_ENTITY_ID] = entity_id
        return service, h_attributes

    @classmethod
    def model_get(cls, hass: HomeAssistant, entity_id: str, entity_attributes: Mapping[str, Any]) -> list:
        supported_features = entity_attributes.get(ATTR_SUPPORTED_FEATURES, 0)
        VLog.info(_TAG, f"[model_get]FanEntityFeature(self.supported_features)={CoverEntityFeature(supported_features)}"
                  f"\n entity_attributes = {entity_attributes}")
        model: list = []
        if (CoverEntityFeature.OPEN & CoverEntityFeature(supported_features)) != 0:
            h_key = "open"
            VLog.info(_TAG, f"[model_get]{entity_id} support {h_key}")
            _open_model = VAttributeUtils.get_model_item(Platform.COVER, h_key)
            if _open_model is not None:
                model.append(_open_model)
        if (CoverEntityFeature.CLOSE & CoverEntityFeature(supported_features)) != 0:
            h_key = "close"
            VLog.info(_TAG, f"[model_get]{entity_id} support {h_key}")
            _close_model = VAttributeUtils.get_model_item(Platform.COVER, h_key)
            if _close_model is not None:
                model.append(_close_model)
        if (CoverEntityFeature.SET_POSITION & CoverEntityFeature(supported_features)) != 0:
            h_key = "current_position"
            VLog.info(_TAG, f"[model_get]{entity_id} support {h_key}")
            _set_position_model = VAttributeUtils.get_model_item(Platform.COVER, h_key)
            if _set_position_model is not None:
                model.append(_set_position_model)
        if (CoverEntityFeature.STOP & CoverEntityFeature(supported_features)) != 0:
            h_key = "stop"
            VLog.info(_TAG, f"[model_get]{entity_id} support {h_key}")
            _stop_model = VAttributeUtils.get_model_item(Platform.COVER, h_key)
            if _stop_model is not None:
                model.append(_stop_model)
        return model
