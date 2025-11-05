"""
Copyright 2024 vivo Mobile Communication Co., Ltd.
Licensed under the Apache License, Version 2.0 (the "License");

   http://www.apache.org/licenses/LICENSE-2.0
"""

import json
import re
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    ATTR_SUPPORTED_FEATURES,
    Platform,
    ATTR_DEVICE_CLASS,
    ATTR_FRIENDLY_NAME,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.components.switch import (
    SwitchDeviceClass,
)
from .const import (
    VIVO_HA_PLATFORM_PK,
    VIVO_HA_PLATFORM_PKY_KEY,
    VIVO_HA_KEY_WORLD_DEV_LOGIC_MAC,
    VIVO_HA_KEY_WORLD_DEV_PHY_MAC,
    VIVO_HA_PLATFORM_MANUFACTURER,
    VIVO_HA_KEY_WORLD_DEV_PROPS,
    VIVO_HA_KEY_WORLD_DEV_EN,
    VIVO_HA_PLATFORM_SOCKET_PK,
    VIVO_HA_PLATFORM_SWITCH_PK,
)
from .v_attritube_map import v2h_attributes_map
from .v_climate_model import VClimateModel
from .v_cover_model import VCoverModel
from .v_fan_model import VFanModel
from .v_light_model import VLightModel
from .v_sensor_model import VSensorModel, VIVO_HA_SENSORS_PK
from .v_switch_model import VSwitchModel
from .v_tv_model import VTVModelUtils
from .v_utils.vlog import VLog

_TAG = "model"


class VModel:
    def __init__(
        self, hass: HomeAssistant, config: ConfigEntry, entity_id: str
    ) -> None:
        self.hass = hass
        self.config = config
        self.entity_id = entity_id
        self.platform = entity_id.split(".")[0]
        self.entity_obj = er.async_get(hass).async_get(entity_id)
        self.model: dict = {}
        if self.entity_obj is None or self.entity_obj.device_id is None:
            VLog.error(_TAG, f"{entity_id}:entity_obj or entity_obj.device_id is None")
            return
        self.device = dr.async_get(hass).async_get(self.entity_obj.device_id)
        self.state = self.hass.states.get(entity_id)
        if self.state is None:
            self.entity_attributes = {}
            self.supported_features = 0
            VLog.error(_TAG, f"{entity_id}: state is None")
        else:
            self.entity_attributes = self.state.attributes
            self.supported_features = self.state.attributes.get(ATTR_SUPPORTED_FEATURES)
        self.common_model = v2h_attributes_map["commom"]
        self.entity_model: list = []
        pky = VIVO_HA_PLATFORM_PK.get(self.platform)
        manufacturer_name: str = "万物互联有限公司"
        self.phyMac: str = self.entity_obj.device_id
        if not self.entity_obj.id:
            self.logicMac = None
        else:
            self.logicMac: str = f"{self.entity_obj.id}.{self.platform}"
        if self.platform == Platform.LIGHT:
            self.entity_model = VLightModel.model_get(
                self.hass, self.entity_id, self.entity_attributes
            )
        elif self.platform == Platform.SWITCH:
            self.entity_model = VSwitchModel.model_get(
                self.hass, self.entity_id, self.entity_attributes
            )
            VLog.info(
                _TAG,
                f"get switch model class:{self.entity_attributes.get(ATTR_DEVICE_CLASS)}",
            )
            device_class = self.entity_attributes.get(ATTR_DEVICE_CLASS)
            if device_class == SwitchDeviceClass.OUTLET:
                pky = VIVO_HA_PLATFORM_SOCKET_PK
            else:
                pky = VIVO_HA_PLATFORM_SWITCH_PK

        elif self.platform == Platform.CLIMATE:
            self.entity_model = VClimateModel.model_get(
                self.hass, self.entity_id, self.entity_attributes
            )
        elif self.platform == Platform.FAN:
            self.entity_model = VFanModel.model_get(
                self.hass, self.entity_id, self.entity_attributes
            )
        elif self.platform == Platform.COVER:
            self.entity_model = VCoverModel.model_get(
                self.hass, self.entity_id, self.entity_attributes
            )
        elif self.platform == Platform.REMOTE:
            self.entity_model = VTVModelUtils.remote_model_get(
                self.hass, self.device, self.entity_attributes
            )
        elif self.platform == Platform.MEDIA_PLAYER:
            self.entity_model = VTVModelUtils.media_play_model_get(
                self.hass, self.device, self.entity_attributes
            )
        elif self.platform in {Platform.SENSOR, Platform.BINARY_SENSOR}:
            self.entity_model = VSensorModel.model_get(
                self.hass, self.entity_id, self.entity_attributes
            )
            pky = VIVO_HA_SENSORS_PK.get(self.entity_attributes.get(ATTR_DEVICE_CLASS))
        else:
            VLog.error(_TAG, f"[init]platform:{self.platform} not support")
            return

        if len(self.entity_model) == 0:
            VLog.warning(
                _TAG,
                f"[init]entity_id:{self.entity_id} attributes:{self.entity_attributes}",
            )
            VLog.warning(_TAG, f"[init]state:{self.state}")
            VLog.warning(_TAG, f"[init]states.state:{self.state.state}")
            return

        self.model[VIVO_HA_PLATFORM_PKY_KEY] = pky
        self.model[VIVO_HA_PLATFORM_MANUFACTURER] = manufacturer_name
        pattern = re.compile(
            r'[^a-zA-Z0-9\u4E00-\u9FA5\u00A5|?:#$/!{}()~<>\'.,;+=_*￥$@%\[\]"&\^《》：；”“’‘【】——，。…\\！]'
        )
        device_name = re.sub(pattern, "", self.state.attributes.get(ATTR_FRIENDLY_NAME))
        if device_name is not None and len(device_name) > 0:
            if len(device_name) > 100:
                self.model[VIVO_HA_KEY_WORLD_DEV_EN] = device_name[:100]
            else:
                self.model[VIVO_HA_KEY_WORLD_DEV_EN] = device_name
        self.model[VIVO_HA_KEY_WORLD_DEV_LOGIC_MAC] = self.logicMac
        self.model[VIVO_HA_KEY_WORLD_DEV_PHY_MAC] = self.phyMac
        self.model[VIVO_HA_KEY_WORLD_DEV_PROPS] = self.common_model + self.entity_model

        try:
            json_str = json.dumps(self.entity_attributes, default=str)
        except Exception as e:
            json_str = f"<json error: {e}>"

        VLog.info(_TAG, f"[init]entity_attributes json :{json_str}")
        VLog.info(_TAG, f"[init]{entity_id} whole_model:{json.dumps(self.model)}")
