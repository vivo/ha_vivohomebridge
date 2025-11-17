"""
Copyright 2024 vivo Mobile Communication Co., Ltd.
Licensed under the Apache License, Version 2.0 (the "License");

   http://www.apache.org/licenses/LICENSE-2.0
"""

import asyncio
import copy
import json
import re
from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.components.cover import CoverDeviceClass
from homeassistant.components.media_player import MediaPlayerDeviceClass
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.components.switch import SwitchDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    ATTR_ENTITY_ID,
    Platform,
    ATTR_FRIENDLY_NAME,
    ATTR_NAME,
    ATTR_DEVICE_CLASS,
    ATTR_TEMPERATURE,
    CONF_UNIT_OF_MEASUREMENT,
    STATE_UNAVAILABLE,
)
from homeassistant.core import HomeAssistant, Event, EventStateChangedData
from homeassistant.helpers import (
    device_registry as dr,
    entity_registry as er,
)
from homeassistant.helpers.device_registry import DeviceEntry
from homeassistant.helpers.storage import Store
from .const import (
    DOMAIN,
    VIVO_HA_BRIDGE_VERSION,
    VIVO_HA_KEY_WORLD_DEV_LOGIC_MAC,
    EVENT_VHOME_DEV_STATE_CHANGE,
    VIVO_DEVICE_NAME_CONFIG_KEY,
    VIVO_DEVICE_ENTITY_ID_KEY,
    VIVO_HA_CONFIG_DATA_DEVICES_KEY,
    VIVO_HA_PLATFORM_PK,
    VIVO_HA_PLATFORM_PKY_KEY,
    VIVO_HA_PLATFORM_SWITCH_PK,
)
from .utils import Utils
from .v_attribute import (
    VIVO_ATTR_NAME_ONLINE,
    VIVO_HA_COMMON_ATTR_LIST,
    VIVO_HA_COMMOM_ATTR_SOFTVER,
    VIVO_HA_COMMOM_ATTR_HARDVER,
    VIVO_HA_COMMOM_ATTR_VENDOR,
    VIVO_HA_COMMON_ATTR_SERIAL,
    VIVO_HA_COMMON_ATTR_MODEL,
    HA_ATTR_NAME_POWER,
    VIVO_KEY_WORD_V_NAME,
    VIVI_KEY_WORK_SENSOR_CLASS,
)

# new device integration
from .v_climate_model import VClimateModel
from .v_cover_model import VCoverModel
from .v_fan_model import VFanModel
from .v_light_model import VLightModel
from .v_sensor_model import VSensorModel, VIVO_HA_SENSORS_PK
from .v_switch_model import VSwitchModel
from .v_tv_model import VTVModel, VTVModelUtils
from .v_utils.vattributes_utils import VAttributeUtils
from .v_utils.vlog import VLog
from .v_water_heater_model import VWaterHeaterModel

"""new device integration"""
VIVO_HA_PLATFORM_SUPPORT_LIST = [
    Platform.LIGHT,
    Platform.SWITCH,
    Platform.CLIMATE,
    Platform.FAN,
    Platform.COVER,
    Platform.BINARY_SENSOR,
    Platform.SENSOR,
]
_TAG = "bridge"


class VBridgeEntity:
    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        """new device integration"""
        self.hass: HomeAssistant = hass
        self.config_entry = config_entry
        self.domain = DOMAIN
        self.bridge_service: DeviceEntry | None = None
        self.device_enable = True
        self.version = VIVO_HA_BRIDGE_VERSION
        self.bridge_config_handle = Store(hass, 1, f"{DOMAIN}/vBridgeConfig.json")
        self.bridge_config_data = []
        self.light_model = VLightModel(hass, config_entry, "lights")
        self.sensor_model = VSensorModel(hass, config_entry, "sensors")
        self.switch_model = VSwitchModel(hass, config_entry, "switch")
        self.climate_model = VClimateModel(hass, config_entry, "climate")
        self.fan_model = VFanModel(hass, config_entry, "fan")
        self.cover_model = VCoverModel(hass, config_entry, "cover")
        self.tv_model = VTVModel(
            hass,
            config_entry,
            [VTVModel.LG_IDENTIFIER_ID, VTVModel.APPLE_IDENTIFIER_ID],
        )
        self.water_heater_model = VWaterHeaterModel(hass, config_entry, "waterHeater")
        VLog.info(_TAG, "[VBridgeEntity] init ... ...")

    def set_device_enable(self, enable: bool) -> None:
        self.device_enable = enable

    def get_device_enable(self) -> bool:
        return self.device_enable

    async def async_handle_entity_state_change(
        self, event: Event[EventStateChangedData]
    ) -> None:
        if event.data.get("old_state") is None or event.data.get("new_state") is None:
            return
        old_state = event.data.get("old_state")
        new_state = event.data.get("new_state")
        entity_id = event.data.get("entity_id")
        old_attrs = old_state.attributes
        new_attrs = new_state.attributes
        changed_attrs = {}
        current_attrs = {}
        current_attrs_from_change = True
        # state change from off to on,then flush all attributes
        if (old_state.state == "off" or old_state == STATE_UNAVAILABLE) and (
            new_state.state != "off" and new_state != STATE_UNAVAILABLE
        ):
            current_attrs_from_change = False
        try:
            def diff_states(old_state, new_state):
                """返回只包含变化项的新属性（包括 state 和 attributes）。"""
                result = {}

                if old_state.state != new_state.state:
                    result["state"] = new_state.state

                old_attrs = old_state.attributes or {}
                new_attrs = new_state.attributes or {}

                for key, new_value in new_attrs.items():
                    if old_attrs.get(key) != new_value:
                        result[key] = new_value

                # 被删除的属性（旧有新无）
                for key in old_attrs:
                    if key not in new_attrs:
                        result[key] = None

                return result


            VLog.info(
                _TAG,
                f"[entity_state_change] {entity_id} from change:{current_attrs_from_change} "
                f"change as follow:\n\t\r old_state:{old_state}\n\n\t\r new_state:{new_state}\n\n"
                f"\t\r old_attrs:{json.dumps(old_attrs,default=str)}\n\n\t\r new_attrs:{json.dumps(new_attrs,default=str)}\n\n",
            )
            current_attrs  = diff_states(old_state,new_state)
        except Exception as e:
            VLog.warning(_TAG, f"<json error: {e}>")
            
            
        if current_attrs_from_change is False:
            for attr_name, new_value in new_attrs.items():
                current_attrs[attr_name] = new_value
        else:
            if changed_attrs:
                VLog.info(
                    _TAG,
                    f"[entity_state_change] {entity_id} had the following attribute changes:",
                )
                for attr_name, attr_value in changed_attrs.items():
                    VLog.info(
                        _TAG,
                        f"[entity_state_change] \t{attr_name}: "
                        f"{attr_value['old']} -> {attr_value['new']}",
                    )

        platform = entity_id.split(".")[0]
        deviceid = Utils.get_device_id(entity_id, self.bridge_config_data)
        if deviceid is None:
            return
        state = self.hass.states.get(entity_id)
        if not state:
            await self.async_notify_device_offline(
                Utils.get_dn(entity_id, self.bridge_config_data)
            )
            return
        attributes_map: list = []
        # new device integration
        if platform == Platform.LIGHT:
            attributes_map = self.light_model.attributes_map
        elif platform == Platform.SWITCH:
            device_class = state.attributes.get(ATTR_DEVICE_CLASS)
            VLog.info(_TAG, f"Switch class:{device_class}")
            if (
                changed_attrs.get("switch.on") is not None
                or new_state.state != old_state.state
            ):
                attributes_map = self.switch_model.attributes_map
            else:
                try:
                    VLog.info(
                        _TAG,
                        f"[entity_state_change] {entity_id} "
                        f"Unsupported the attrs:{json.dumps(changed_attrs,default=str)}",
                    )
                except Exception as e:
                    VLog.warning(_TAG, f"<json error: {e}>")
                return
            if new_state.state != old_state.state:
                current_attrs["power"] = new_state.state
        elif platform == Platform.CLIMATE:
            attributes_map = self.climate_model.attributes_map
            self.climate_model.calibrate_current_attrs(
                current_attrs, new_state.state, old_state.state
            )
        elif platform == Platform.FAN:
            attributes_map = self.fan_model.attributes_map
        elif platform == Platform.COVER:
            attributes_map = self.cover_model.attributes_map
        elif platform == Platform.WATER_HEATER:
            attributes_map = self.water_heater_model.attributes_map
        elif platform == Platform.MEDIA_PLAYER:
            _current_attrs, _attributes_list = (
                VTVModelUtils.get_media_player_attribute_list_and_state(
                    entity_id,
                    old_state.state,
                    new_state.state,
                    self.hass,
                    self.tv_model,
                )
            )
            if _attributes_list is None or len(_attributes_list) == 0:
                VLog.info(
                    _TAG, f"[entity_state_change] No attributes list for {entity_id}"
                )
                return
            attributes_map = _attributes_list
            if _current_attrs is not None and len(_current_attrs) != 0:
                for attr_name, attr_value in _current_attrs.items():
                    current_attrs[attr_name] = attr_value
        elif platform == Platform.REMOTE:
            _current_attrs, _attributes_list = (
                VTVModelUtils.get_remote_attribute_list_and_state(
                    entity_id,
                    old_state.state,
                    new_state.state,
                    self.hass,
                    self.tv_model,
                )
            )
            if _attributes_list is None or len(_attributes_list) == 0:
                VLog.info(
                    _TAG,
                    f"[entity_state_change] No attributes list for {entity_id} of {platform}",
                )
                return
            attributes_map = _attributes_list
            if _current_attrs is not None and len(_current_attrs) != 0:
                for attr_name, attr_value in _current_attrs.items():
                    current_attrs[attr_name] = attr_value
        elif platform == Platform.BINARY_SENSOR or platform == Platform.SENSOR:
            attributes_maps = self.sensor_model.attributes_map
            device_class = state.attributes.get(ATTR_DEVICE_CLASS)
            target_map = next( item 
                                    for item in attributes_maps
                                    if item[VIVI_KEY_WORK_SENSOR_CLASS] ==device_class 
                                    )
            attributes_map.append(target_map)
            unit = new_attrs.get(CONF_UNIT_OF_MEASUREMENT)
            if device_class == SensorDeviceClass.TEMPERATURE:
                current_attrs["state"] = VSensorModel.sensor_h2v_val(
                    device_class, unit, new_state.state
                )
        else:
            VLog.warning(_TAG, f"{entity_id} Unsupported platform:{platform}")
            return
        VLog.info(_TAG, f"[entity_state_change] current_attrs:{current_attrs}")
        v_attrs = {}
        try:
            v_attrs = VAttributeUtils.h2v_attributes_converter(
                self.hass, entity_id, attributes_map, current_attrs, False
            )
        except Exception as e:
            VLog.warning(_TAG, f"[entity_state_change] {entity_id} convert error:{e}")
        if new_state.state == STATE_UNAVAILABLE:
            v_attrs = {"online": "false"}
        else:
            v_attrs["online"] = "true"
        VLog.info(_TAG, f"[entity_state_change] v_attrs:{v_attrs}")
        if len(v_attrs) == 0:
            return
        self.hass.bus.async_fire(
            EVENT_VHOME_DEV_STATE_CHANGE,
            {
                "data": v_attrs,
                VIVO_DEVICE_NAME_CONFIG_KEY: Utils.get_dn(
                    entity_id, self.bridge_config_data
                ),
                "domain": DOMAIN,
            },
        )

    async def async_notify_device_offline(self, dn: str):
        self.hass.bus.async_fire(
            EVENT_VHOME_DEV_STATE_CHANGE,
            {
                "data": {"online": "false"},
                VIVO_DEVICE_NAME_CONFIG_KEY: dn,
                "domain": DOMAIN,
            },
        )

    async def _async_get_entity_ids_names(self, platforms: list):
        """new device integration"""
        _id_name_dict_list: list[dict[str, str]] = []
        if platforms is None:
            _entity_ids = await self.hass.async_add_executor_job(
                self.hass.states.async_entity_ids, None
            )
            for entity_id in _entity_ids:
                _item: dict = {}
                _device_name = self.hass.states.get(entity_id).attributes.get(
                    ATTR_FRIENDLY_NAME
                )
                _item[ATTR_ENTITY_ID] = entity_id
                temp_name = self._generate_device_name(_device_name, "", entity_id)
                if not temp_name:
                    continue
                else:
                    _item[ATTR_NAME] = temp_name
                _id_name_dict_list.append(_item)
        else:
            for platform in platforms:
                VLog.info(_TAG, f"[async_get_entity_ids_names]platform:{platform}")
                entity_ids = await self.hass.async_add_executor_job(
                    self.hass.states.async_entity_ids, platform
                )
                if platform == Platform.SWITCH:
                    for entity_id in entity_ids:
                        device_class = self.hass.states.get(entity_id).attributes.get(
                            ATTR_DEVICE_CLASS
                        )
                        _item: dict = {}
                        _device_name = self.hass.states.get(entity_id).attributes.get(
                            ATTR_FRIENDLY_NAME
                        )
                        _item[ATTR_ENTITY_ID] = entity_id
                        VLog.info(
                            _TAG,
                            f"Switch name={_device_name},entity_id={entity_id} device_class={device_class}",
                        )
                        if device_class == SwitchDeviceClass.OUTLET:
                            _item[VIVO_HA_PLATFORM_PKY_KEY] = VIVO_HA_PLATFORM_PK.get(
                                platform
                            )
                        else:
                            _item[VIVO_HA_PLATFORM_PKY_KEY] = VIVO_HA_PLATFORM_SWITCH_PK
                        temp_name = self._generate_device_name(
                            _device_name, platform, entity_id
                        )
                        if not temp_name:
                            continue
                        _item[ATTR_NAME] = temp_name
                        _id_name_dict_list.append(_item)

                elif platform == Platform.COVER:
                    for entity_id in entity_ids:
                        device_class = self.hass.states.get(entity_id).attributes.get(
                            ATTR_DEVICE_CLASS
                        )
                        if device_class == CoverDeviceClass.CURTAIN:
                            _item: dict = {}
                            _device_name = self.hass.states.get(
                                entity_id
                            ).attributes.get(ATTR_FRIENDLY_NAME)
                            _item[VIVO_HA_PLATFORM_PKY_KEY] = VIVO_HA_PLATFORM_PK.get(
                                platform
                            )
                            _item[ATTR_ENTITY_ID] = entity_id
                            temp_name = self._generate_device_name(
                                _device_name, platform, entity_id
                            )
                            if not temp_name:
                                continue
                            else:
                                _item[ATTR_NAME] = temp_name
                            _id_name_dict_list.append(_item)
                elif platform == Platform.SENSOR:
                    for entity_id in entity_ids:
                        device_class = self.hass.states.get(entity_id).attributes.get(
                            ATTR_DEVICE_CLASS
                        )
                        if (
                            device_class == SensorDeviceClass.TEMPERATURE
                            or device_class == SensorDeviceClass.HUMIDITY
                            or device_class == SensorDeviceClass.ILLUMINANCE
                            or device_class == SensorDeviceClass.ENUM
                        ):
                            """只支持温度、湿度、光照支持"""
                            _item: dict = {}
                            _device_name = self.hass.states.get(
                                entity_id
                            ).attributes.get(ATTR_FRIENDLY_NAME)
                            _item[ATTR_ENTITY_ID] = entity_id
                            _item[VIVO_HA_PLATFORM_PKY_KEY] = VIVO_HA_SENSORS_PK.get(
                                device_class
                            )
                            temp_name = self._generate_device_name(
                                _device_name, platform, entity_id
                            )
                            if not temp_name:
                                continue
                            else:
                                _item[ATTR_NAME] = temp_name
                                _id_name_dict_list.append(_item)
                elif platform == Platform.BINARY_SENSOR:
                    for entity_id in entity_ids:
                        device_class = self.hass.states.get(entity_id).attributes.get(
                            ATTR_DEVICE_CLASS
                        )
                        if (
                            device_class == BinarySensorDeviceClass.OCCUPANCY
                            or device_class == BinarySensorDeviceClass.DOOR
                            or device_class == BinarySensorDeviceClass.GARAGE_DOOR
                            or device_class == BinarySensorDeviceClass.OPENING
                            or device_class == BinarySensorDeviceClass.MOTION
                            or device_class == BinarySensorDeviceClass.MOVING
                        ):
                            _item: dict = {}
                            _device_name = self.hass.states.get(
                                entity_id
                            ).attributes.get(ATTR_FRIENDLY_NAME)
                            _item[ATTR_ENTITY_ID] = entity_id
                            _item[VIVO_HA_PLATFORM_PKY_KEY] = VIVO_HA_SENSORS_PK.get(
                                device_class
                            )
                            temp_name = self._generate_device_name(
                                _device_name, platform, entity_id
                            )
                            if not temp_name:
                                continue
                            else:
                                _item[ATTR_NAME] = temp_name
                            _id_name_dict_list.append(_item)
                elif platform == Platform.MEDIA_PLAYER:
                    for entity_id in entity_ids:
                        device_class = self.hass.states.get(entity_id).attributes.get(
                            ATTR_DEVICE_CLASS
                        )
                        if device_class == MediaPlayerDeviceClass.TV:
                            _item: dict = {}
                            _device_name = self.hass.states.get(
                                entity_id
                            ).attributes.get(ATTR_FRIENDLY_NAME)
                            _item[VIVO_HA_PLATFORM_PKY_KEY] = VIVO_HA_PLATFORM_PK.get(
                                platform
                            )
                            _item[ATTR_ENTITY_ID] = entity_id
                            temp_name = self._generate_device_name(
                                _device_name, platform, entity_id
                            )
                            if not temp_name:
                                continue
                            else:
                                _item[ATTR_NAME] = temp_name
                            _id_name_dict_list.append(_item)
                        else:
                            VLog.info(
                                _TAG,
                                f"{entity_id} is not support media player device class:{device_class}",
                            )
                else:
                    for entity_id in entity_ids:
                        _item: dict = {}
                        _device_name = self.hass.states.get(entity_id).attributes.get(
                            ATTR_FRIENDLY_NAME
                        )
                        _item[VIVO_HA_PLATFORM_PKY_KEY] = VIVO_HA_PLATFORM_PK.get(
                            platform
                        )
                        _item[ATTR_ENTITY_ID] = entity_id
                        temp_name = self._generate_device_name(
                            _device_name, platform, entity_id
                        )
                        if not temp_name:
                            continue
                        else:
                            _item[ATTR_NAME] = temp_name
                        _id_name_dict_list.append(_item)
        return _id_name_dict_list

    def _generate_device_name(
        self, default_original_name: str, platform_name: str, entity_id: str
    ) -> str | None:
        hass = self.hass
        _entity_obj = er.async_get(hass).async_get(entity_id)
        if (
            _entity_obj is None
            or _entity_obj.config_entry_id is None
            or len(_entity_obj.config_entry_id) == 0
        ):
            VLog.info(_TAG, f"[generate_device_name] {entity_id} no config entry")
            return None
        if not _entity_obj.id:
            VLog.info(_TAG, f"[generate_device_name] {entity_id} no id")
            return None
        if not default_original_name:
            VLog.info(_TAG, f"[generate_device_name] {entity_id} no name")
            return None
        if len(default_original_name) > 100:
            _result = default_original_name[:100]
        else:
            _result = default_original_name
        if _entity_obj is not None and _entity_obj.device_id:
            _device_id = _entity_obj.device_id
            _device = dr.async_get(hass).async_get(_device_id)
        if platform_name:
            _result += f" ({platform_name})"
        return _result

    async def get_supported_list(self) -> list[dict[str, str]]:
        return await self._async_get_entity_ids_names(VIVO_HA_PLATFORM_SUPPORT_LIST)

    async def async_get_unregister_devices(self) -> list[str] | None:
        unregister_devices = []
        config_devices = self.config_entry.data.get(VIVO_HA_CONFIG_DATA_DEVICES_KEY, {})
        configured_entity_ids = [device[ATTR_ENTITY_ID] for device in config_devices]
        options_source_list = await self.get_supported_list()
        VLog.debug(
            _TAG,
            f"[async_get_unregister_devices] options_source_list:{options_source_list}",
        )
        VLog.debug(
            _TAG,
            f"[async_get_unregister_devices] configured_entity_ids:{configured_entity_ids}",
        )
        # 过滤掉已配置的设备
        unregister_devices = [
            option
            for option in options_source_list
            if option[ATTR_ENTITY_ID] not in configured_entity_ids
        ]
        if len(unregister_devices) > 0:
            index: int = 0
            pattern = re.compile(
                r'[^a-zA-Z0-9\u4E00-\u9FA5\u00A5|?:#$/!{}()~<>\'.,;+=_*￥$@%\[\]"&\^《》：；”“’‘【】——，。…\\！]'
            )
            VLog.debug(_TAG, "unregister_devices list ----------------------")
            for item in unregister_devices:
                entity_obj: er.RegistryEntry = er.async_get(self.hass).async_get(
                    item[ATTR_ENTITY_ID]
                )
                VLog.debug(_TAG, f"{index} : {item[ATTR_ENTITY_ID]}")
                index = index + 1
                item[VIVO_HA_KEY_WORLD_DEV_LOGIC_MAC] = (
                    f"{entity_obj.id}.{item[ATTR_ENTITY_ID].split('.')[0]}"
                )
                item[ATTR_NAME] = re.sub(pattern, "", item[ATTR_NAME])
                if entity_obj.id is not None:
                    del item[ATTR_ENTITY_ID]

        return unregister_devices

    def flush_device_status(self, reason: str, device: dict):
        """new device integration"""
        device_entity_id = device[VIVO_DEVICE_ENTITY_ID_KEY]
        device_state = self.hass.states.get(device_entity_id)
        VLog.info(_TAG, f"[flush][{reason}][{device_entity_id}] {device_state}")
        if device_state is not None:
            attributes_map: list = []
            attributes = copy.deepcopy(dict(device_state.attributes))
            device_platform = device[VIVO_HA_KEY_WORLD_DEV_LOGIC_MAC].split(".")[1]
            VLog.info(_TAG, f"[flush] device platform:{device_platform}")
            if device_platform == Platform.LIGHT:
                attributes_map = self.light_model.attributes_map
            elif device_platform == Platform.SWITCH:
                attributes_map = self.switch_model.attributes_map
            elif device_platform == Platform.CLIMATE:
                attributes_map = self.climate_model.attributes_map
                attributes["state"] = device_state.state
                self.climate_model.calibrate_swing_mode_attr_when_flush(attributes)
            elif device_platform == Platform.FAN:
                attributes_map = self.fan_model.attributes_map
                attributes["state"] = device_state.state
            elif device_platform == Platform.COVER:
                attributes_map = self.cover_model.attributes_map
            elif device_platform == Platform.MEDIA_PLAYER:
                _attributes_list = VTVModelUtils.get_media_player_attributes_list(
                    device_entity_id, self.hass, self.tv_model
                )
                attributes["state"] = device_state.state
                attributes[HA_ATTR_NAME_POWER] = device_state.state
                if _attributes_list is not None and len(_attributes_list) != 0:
                    attributes_map = _attributes_list
            elif device_platform == Platform.REMOTE:
                attributes["state"] = device_state.state
                attributes[HA_ATTR_NAME_POWER] = device_state.state
                _attributes_list = VTVModelUtils.get_remote_device_attribute_list(
                    device_entity_id, self.hass, self.tv_model
                )
                if _attributes_list is not None and len(_attributes_list) != 0:
                    attributes_map = _attributes_list
            elif (
                device_platform == Platform.SENSOR
                or device_platform == Platform.BINARY_SENSOR
            ):
                attributes_maps = self.sensor_model.attributes_map
                device_class = attributes.get(ATTR_DEVICE_CLASS)
                target_map = next( item 
                                      for item in attributes_maps
                                      if item[VIVI_KEY_WORK_SENSOR_CLASS] ==device_class 
                                      )
                attributes_map.append(target_map)
                unit = attributes.get(CONF_UNIT_OF_MEASUREMENT)
                if device_class == SensorDeviceClass.TEMPERATURE:
                    attributes["state"] = self.sensor_model.sensor_h2v_val(
                        device_class, unit, device_state.state
                    )
                else:
                    attributes["state"] = device_state.state
            elif device_platform == Platform.WATER_HEATER:
                attributes_map = self.water_heater_model.attributes_map
                attributes["state"] = device_state.state
            else:
                VLog.info(_TAG, f"[flush] not support :{device_platform}")
                return
            try:
                VLog.info(
                    _TAG, "[flush] Attribute before transform: " + json.dumps(attributes,default=str)
                )
            except Exception as e:
                VLog.warning(_TAG, f"<json error: {e}>")
            vivo_std_attrs = {}
            try:
                vivo_std_attrs = VAttributeUtils.h2v_attributes_converter(
                    self.hass,
                    device[VIVO_DEVICE_ENTITY_ID_KEY],
                    attributes_map,
                    attributes,
                    True,
                )
            except Exception as e:
                VLog.warning(_TAG, f"[flush] converter exception :{e}")
            vivo_std_common_attrs = self._sub_dev_common_attributes_get(
                entity_id=device[VIVO_DEVICE_ENTITY_ID_KEY]
            )
            if vivo_std_common_attrs is not None:
                vivo_std_attrs.update(vivo_std_common_attrs)
            else:
                VLog.warning(_TAG, "[flush] no common attribute to be found")

            if device_state.state == "unavailable":
                vivo_std_attrs = {VIVO_ATTR_NAME_ONLINE: "false"}
            else:
                vivo_std_attrs[VIVO_ATTR_NAME_ONLINE] = "true"
            try:
                VLog.info(
                    _TAG, "[flush] Attribute after transform: " + json.dumps(vivo_std_attrs,default=str)
                )
            except Exception as e:
                VLog.warning(_TAG, f"<json error: {e}>")
            self.hass.bus.fire(
                EVENT_VHOME_DEV_STATE_CHANGE,
                {
                    "data": vivo_std_attrs,
                    VIVO_DEVICE_NAME_CONFIG_KEY: device[VIVO_DEVICE_NAME_CONFIG_KEY],
                    "domain": DOMAIN,
                },
            )
        else:
            # 被禁用了
            vivo_std_attrs = {}
            vivo_std_attrs = {VIVO_ATTR_NAME_ONLINE: "false"}
            self.hass.bus.fire(
                EVENT_VHOME_DEV_STATE_CHANGE,
                {
                    "data": vivo_std_attrs,
                    VIVO_DEVICE_NAME_CONFIG_KEY: device[VIVO_DEVICE_NAME_CONFIG_KEY],
                    "domain": DOMAIN,
                },
            )

    def _sub_dev_common_attributes_get(self, entity_id: str) -> dict | None:
        common_attributes = {}
        entity_obj: er.RegistryEntry = er.async_get(self.hass).async_get(entity_id)
        if entity_obj is None or entity_obj.device_id is None:
            return common_attributes
        device: dr.DeviceEntry = dr.async_get(self.hass).async_get(entity_obj.device_id)
        for item in VIVO_HA_COMMON_ATTR_LIST:
            if item == VIVO_HA_COMMOM_ATTR_SOFTVER:
                if device.sw_version is not None and device.sw_version != "":
                    common_attributes[item] = device.sw_version
                else:
                    common_attributes[item] = "Unknown"
            elif item == VIVO_HA_COMMOM_ATTR_HARDVER:
                if device.hw_version is not None and device.hw_version != "":
                    common_attributes[item] = device.hw_version
                else:
                    common_attributes[item] = "Unknown"
            elif item == VIVO_HA_COMMOM_ATTR_VENDOR:
                if device.manufacturer is not None and device.manufacturer != "":
                    common_attributes[item] = device.manufacturer
                else:
                    common_attributes[item] = "Unknown"
            elif item == VIVO_HA_COMMON_ATTR_SERIAL:
                if device.serial_number is not None and device.serial_number != "":
                    common_attributes[item] = device.serial_number
                else:
                    common_attributes[item] = "Unknown"
            elif item == VIVO_HA_COMMON_ATTR_MODEL:
                if device.model is not None and device.model != "":
                    common_attributes[item] = device.model
                else:
                    common_attributes[item] = "Unknown"
            else:
                continue
        return common_attributes

    async def async_sub_dev_attributes_set(self, dname: str, v_attributes: dict):
        entity_id = Utils.get_entity_id_by_name(dname, self.bridge_config_data)
        deviceid = Utils.get_device_id_by_name(dname, self.bridge_config_data)
        VLog.info(
            _TAG, f"[sub_dev_attributes_set]:entity_id:{entity_id}:{dname}:{deviceid}"
        )
        if entity_id is None:
            return
        if deviceid is None:
            return
        if entity_id is None:
            return
        onoff = self.hass.states.get(entity_id).state

        if onoff == "unavailable":
            VLog.info(_TAG, f"{dname} is unavailable")
            return
        platform = entity_id.split(".")[0]
        if platform not in VIVO_HA_PLATFORM_SUPPORT_LIST:
            VLog.warning(_TAG, f"Unsupported platform:{platform}")
            return
        await self._v2h_states_set(platform, entity_id, v_attributes)

    async def _v2h_states_set(self, domain: str, entity_id: str, attributes):
        """new device integration"""
        attributes_map: list = []
        if domain == Platform.LIGHT:
            attributes_map = self.light_model.attributes_map
        elif domain == Platform.SWITCH:
            attributes_map = self.switch_model.attributes_map
        elif domain == Platform.CLIMATE:
            attributes_map = self.climate_model.attributes_map
        elif domain == Platform.FAN:
            attributes_map = self.fan_model.attributes_map
        elif domain == Platform.COVER:
            attributes_map = self.cover_model.attributes_map
        elif domain == Platform.MEDIA_PLAYER:
            attributes_map = VTVModelUtils.get_media_player_attributes_list(
                entity_id, self.hass, self.tv_model
            )
            if attributes_map is None or len(attributes_map) == 0:
                VLog.info(_TAG, f"no attribute {domain} for {entity_id}")
                return
        elif domain == Platform.REMOTE:
            attributes_map = VTVModelUtils.get_remote_device_attribute_list(
                entity_id, self.hass, self.tv_model
            )
            if attributes_map is None or len(attributes_map) == 0:
                VLog.info(_TAG, f"no attribute {domain} for {entity_id}")
                return
        elif domain == Platform.WATER_HEATER:
            attributes_map = self.water_heater_model.attributes_map
        else:
            VLog.info(_TAG, f"not support {domain}")
            return
        VLog.info(
            _TAG,
            f"[v2h_states_set]entity_id:{entity_id},domain:{domain},attributes:{attributes}",
        )
        _task_index = 0
        for key, val in attributes.items():
            obj = next(
                (
                    item
                    for item in attributes_map
                    if item.get(VIVO_KEY_WORD_V_NAME) == key
                ),
                None,
            )
            VLog.info(_TAG, f"[v2h_states_set]key:{key},value:{val},obj:{obj}")
            if obj:
                v2h_converter = obj["v2h_converter"]
                _service = None
                _h_attributes = None
                _target_domain = None
                if v2h_converter:
                    _service, _temp_attributes = v2h_converter(entity_id, 0, obj, val)
                    if _service is None or _temp_attributes is None:
                        continue
                    _target_domain = _temp_attributes.get("target_domain", None)
                    keys_to_filter = {"target_domain"}
                    _h_attributes = {
                        k: v
                        for k, v in _temp_attributes.items()
                        if k not in keys_to_filter
                    }
                    if _target_domain is None:
                        _target_domain = domain
                    VLog.info(
                        _TAG,
                        f"[v2h_states_set]domain:{_target_domain},service:{_service},"
                        f"h_attributes:{_h_attributes}",
                    )
                    _task_index += 1
                    if _task_index > 1:
                        try:
                            await asyncio.sleep(2)
                        except asyncio.CancelledError as e:
                            VLog.info(_TAG, f"[v2h_states_set] exception:{e}")
                    self.hass.async_create_task(
                        self.hass.services.async_call(
                            _target_domain, _service, _h_attributes, context=None
                        )
                    )
                else:
                    VLog.warning(_TAG, f"[v2h_states_set] no convert method for {key}")
            else:
                VLog.warning(
                    _TAG, f"[v2h_states_set] {key} no contain to {attributes_map}"
                )
