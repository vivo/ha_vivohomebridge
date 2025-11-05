"""
Copyright 2024 vivo Mobile Communication Co., Ltd.
Licensed under the Apache License, Version 2.0 (the "License");

   http://www.apache.org/licenses/LICENSE-2.0
"""

import json
from dataclasses import dataclass
from typing import Any, Optional, Callable, Dict
import asyncio
import time
from enum import Enum
from homeassistant.loader import async_get_integration
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    ATTR_FRIENDLY_NAME,
    __version__,
    ATTR_ENTITY_ID,
    ATTR_NAME,
)
from homeassistant.core import (
    CALLBACK_TYPE,
    HomeAssistant,
    Event,
    HassJobType,
    callback,
)
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import (
    device_registry as dr,
    entity_registry as er,
)
from homeassistant.helpers.device_registry import (
    DeviceEntry,
    EventDeviceRegistryUpdatedData,
)
from homeassistant.helpers.event import async_call_later
from homeassistant.helpers.entity_registry import EVENT_ENTITY_REGISTRY_UPDATED
from homeassistant.helpers.event import (
    async_track_state_change_event,
    async_track_device_registry_updated_event,
)
from .connect_manager import ReconnectManager
from .const import (
    VIVO_BRIDGE_DEVICE_NAME_CONFIG_KEY,
    VIVO_BRIDGE_MAC_CONFIG_KEY,
    VIVO_HA_CONFIG_DATA_DEVICES_KEY,
    VIVO_BRIDGE_HOST_CONFIG_KEY,
    VIVO_BRIDGE_PORT_CONFIG_KEY,
    VIVO_BRIDGE_USER_CODE_CONFIG_KEY,
    EVENT_VHOME_DEV_SET_STATUS,
    EVENT_VHOME_DEV_REMOVE_BRIDGE,
    EVENT_VHOME_DEV_UNREG_RESULT,
    EVENT_VHOME_DEV_REG_RESULT,
    EVENT_VHOME_DEV_ADD,
    EVENT_VHOME_DEV_STATE_CHANGE,
    EVENT_VHOME_DEV_STATE_FLUSH,
    VIVO_HA_KEY_WORLD_DEV_LOGIC_MAC,
    VIVO_DEVICE_NAME_CONFIG_KEY,
    VIVO_DEVICE_ENTITY_ID_KEY,
    DOMAIN,
    EVEVT_VHOME_BRIDGE_ONLINE,
    GLOB_NAME,
    EVENT_VHOME_RECONNECT,
    VIVO_HA_BRIDGE_VERSION,
    VIVO_BRIDGE_DEVICE_ID_CLOUD_KEY,
    EVENT_VHOME_DEV_DEL,
    VIVO_HA_KEY_WORLD_DEV_ENTRY_ID,
    VIVO_DEVICE_NAME_FRIENDLY_KEY,
    VIVO_DEVICE_ID_KEY,
    VIVO_HA_CONF_BIND_CODE,
    VIVO_HA_CONF_ADDABLE_DEVS,
    VHOME_URL,
)
from .py_vhome.vhome import VHome
from .utils import Utils
from .v_attribute import (
    VIVO_HA_COMMON_ATTR_MODEL,
    VIVO_ATTR_NAME_ONLINE,
    VIVO_HA_COMMOM_ATTR_SOFTVER,
    VIVO_HA_COMMOM_ATTR_HARDVER,
    VIVO_HA_COMMOM_ATTR_VENDOR,
    VIVO_HA_COMMON_ATTR_SERIAL,
)
from .v_utils.vlog import VLog
from .vbridge import VBridgeEntity, VIVO_HA_PLATFORM_SUPPORT_LIST
from .vmodel import VModel
from .v_local_service import VLocalService

_TAG = "device_manager"


@dataclass
class VBridgeDevice:
    name: str
    mac: str
    host: str
    port: int
    user_code: str


class DeviceManager:
    class VConfig_STATE(Enum):
        STATE_INIT = 0  # 初始状态
        STATE_LAN = 1  # 局域网配置状态
        STATE_QRCODE = 2  # 扫描配置状态

    _instance = None
    _integration_enable: bool
    _vhome: VHome
    _delayed_job = None
    _config_state: VConfig_STATE
    _bcode_task: Optional[asyncio.Task] = None
    _isbinding_pending: bool = False
    _local_server: VLocalService | None
    _reconnector: ReconnectManager
    _bridge_entity: VBridgeEntity | None
    _registered_device_mac_list: list
    _cancel_listen_add_device: Optional[CALLBACK_TYPE]
    _cancel_listen_state_change: Optional[CALLBACK_TYPE]
    _cancel_listen_state_flush: Optional[CALLBACK_TYPE]
    _cancel_listen_dev_reg: Optional[CALLBACK_TYPE]
    _cancel_listen_dev_unreg: Optional[CALLBACK_TYPE]
    _cancel_listen_set_status: Optional[CALLBACK_TYPE]
    _cancel_listen_bridge_remove: Optional[CALLBACK_TYPE]
    _cancel_listen_bridge_online: Optional[CALLBACK_TYPE]
    _cancel_listen_reconnect: Optional[CALLBACK_TYPE]
    _cancel_ha_state_changed_listener_dict: Dict[str, Optional[Callable[[], None]]]
    _cancel_listen_entity_registry_updated: Optional[CALLBACK_TYPE]
    _cancel_listen_device_registry_updated_dict: Dict[str, Optional[Callable[[], None]]]
    _cancel_listen_delete_device: Optional[CALLBACK_TYPE]
    __BRIDGE_DEVICE_REMOVED_CODE = 5
    integration_version: str = "0.0.0.0"

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(DeviceManager, cls).__new__(cls, *args, **kwargs)
            cls._instance.__initialize()
        return cls._instance

    def __initialize(self):
        self._vhome = VHome(
            VHOME_URL,
            self._on_vhome_state_changed_callback,
            self._on_vhome_data_received_callback,
            self._on_vhome_local_event_callback,
        )
        self.integration_version = "0.0.0.0"
        self._config_state = self.VConfig_STATE.STATE_INIT
        self._local_server = None
        self._reconnector = ReconnectManager(self._vhome)
        self._bridge_entity = None
        self._integration_enable = True
        self._registered_device_mac_list = []
        self._cancel_listen_add_device = None
        self._cancel_listen_state_change = None
        self._cancel_listen_state_flush = None
        self._cancel_listen_dev_reg = None
        self._cancel_listen_dev_unreg = None
        self._cancel_listen_set_status = None
        self._cancel_listen_bridge_remove = None
        self._cancel_listen_bridge_online = None
        self._cancel_listen_reconnect = None
        self._cancel_listen_entity_registry_updated = None
        self._cancel_listen_delete_device = None
        self._cancel_listen_device_registry_updated_dict = {}
        self._cancel_ha_state_changed_listener_dict = {}

    @classmethod
    def instance(cls):
        if not cls._instance:
            cls._instance = cls()
        return cls._instance

    def set_config_state(self, state: int):
        self._config_state = state

    def get_config_state(self) -> VConfig_STATE:
        return self._config_state

    def set_bridge(self, bridge_entity: VBridgeEntity) -> None:
        """Initialize this attribute as early as possible"""
        self._integration_enable = True
        self._registered_device_mac_list = []
        self._bridge_entity = bridge_entity
        self._register_events_listener(bridge_entity.hass)
        VLog.info(_TAG, f"[set_bridge]：bridge has been set")

    def set_local_service(self, hass: HomeAssistant) -> None:
        if self.get_bridge_mac() is None:
            raise ValueError("The 'mac' parameter cannot be None.")
        self._local_server = VLocalService(
            hass, GLOB_NAME, self.integration_version, self.get_bridge_mac()
        )

    async def async_load_config(self):
        if self._bridge_entity is None:
            VLog.info(_TAG, f"[load_config]：bridge has not initialized yet")
            return
        VLog.info(_TAG, "[async_load_config] start ...")
        try:
            self._bridge_entity.bridge_config_data = (
                await self._bridge_entity.bridge_config_handle.async_load() or []
            )
            VLog.debug(
                _TAG, f"bridge_config_data:{self._bridge_entity.bridge_config_data}"
            )
        except (ValueError, HomeAssistantError):
            await self._bridge_entity.bridge_config_handle.async_remove()
            self._bridge_entity.bridge_config_data = []
        if self._bridge_entity.bridge_config_data:
            VLog.info(
                _TAG,
                f"[async_load_config]"
                f" bridge_config_data:{json.dumps(self._bridge_entity.bridge_config_data)}",
            )
        for item in self._bridge_entity.bridge_config_data:
            entity_id_from_config = item.get(VIVO_DEVICE_ENTITY_ID_KEY)
            if entity_id_from_config:
                if (
                    self._cancel_ha_state_changed_listener_dict.get(
                        entity_id_from_config
                    )
                    is None
                ):
                    VLog.info(
                        _TAG,
                        f"[async_load_config] add {entity_id_from_config} state change listener",
                    )
                    self._cancel_ha_state_changed_listener_dict[
                        entity_id_from_config
                    ] = async_track_state_change_event(
                        self._bridge_entity.hass,
                        entity_id_from_config,
                        self._bridge_entity.async_handle_entity_state_change,
                        job_type=HassJobType.Coroutinefunction,
                    )
                else:
                    VLog.info(
                        _TAG,
                        f"[async_load_config] {entity_id_from_config} state change listener already exists",
                    )
        await self._async_set_config_devices("init")

    async def async_dm_service_start(
        self, hass: HomeAssistant, isNeed_to_update_mdns: bool = False
    ):
        await self.async_load_config()
        integration = await async_get_integration(hass, DOMAIN)
        self.integration_version = integration.manifest["version"]
        bridge_device = self.get_bridge_device()
        VLog.debug(_TAG, f"async_dm_service_start bridge_device={bridge_device}")
        self.get_local_server().config_flag(0)
        await self.get_vhome().network_shakehand_task_stop()
        self.get_local_server().config_dn(None)
        self.get_local_server().config_ver(self.integration_version)
        if bridge_device.name is not None and len(bridge_device.name) > 0:
            VLog.info(_TAG, f"[setup task] init bridge {bridge_device}")
            entity_id = self._bridge_entity.config_entry.entry_id
            self.create_update_service(
                hass, bridge_device.name, bridge_device.mac, entity_id
            )
            self.get_local_server().config_dn(bridge_device.name)
            if (
                self.get_bridge_entity().get_device_enable()
                and bridge_device.host is not None
                and len(bridge_device.host) > 0
                and bridge_device.port is not None
                and len(bridge_device.port) > 0
            ):
                self.get_local_server().config_flag(1)
                await self.async_connect(
                    bridge_device.host,
                    int(bridge_device.port),
                    bridge_device.name,
                    bridge_device.user_code,
                    "setup",
                )
            else:
                VLog.info(_TAG, f"[async_dm_service_start] bridge is disable")
        else:
            await self.get_vhome().network_shakehand_task_start()

        if isNeed_to_update_mdns is True:
            await self.get_local_server().sync_update_txt()
        else:
            target_port: int = self.get_vhome().get_local_net_target_port()
            await self.get_local_server().sync_start(target_port)

        VLog.info(_TAG, f"[async_dm_service_start] done")

    async def async_connect(
        self, host: str, port: int, dn: str, user_code: str, reason: str
    ) -> None:
        if self._reconnector.is_reconnect_task_active():
            await self._reconnector.stop_reconnect(reason)
        await self._reconnector.async_connect(host, port, dn, user_code, reason)

    async def async_sync_sub_devices(
        self, config_entry: ConfigEntry, reason: str
    ) -> None:
        """sync local sub devices to server"""
        device_list = self.get_device_list(config_entry)
        VLog.info(_TAG, f"[async_sync_sub_devices][{reason}] {device_list}")
        if "setup" == reason:
            await self._async_sync_sub_devices(config_entry, device_list)
        else:
            is_update = True
            if is_update:
                await self._async_sync_sub_devices(config_entry, device_list)
            else:
                VLog.info(
                    _TAG,
                    f"[async_sync_sub_devices] device list not update for {reason}",
                )

    async def async_data_report(self, target_id: str | None, props: dict):
        if self._bridge_entity is None:
            VLog.info(_TAG, f"[async_data_report] bridge has not initialized yet")
            return
        if not self._bridge_entity.get_device_enable():
            VLog.info(
                _TAG,
                f"[async_data_report] target_id {target_id} but bridge has not enabled",
            )
            return

        VLog.info(_TAG, f"[async_data_report] target_id {target_id},props:{props}")
        bridge_name = self._bridge_entity.config_entry.data.get(
            VIVO_BRIDGE_DEVICE_NAME_CONFIG_KEY
        )
        if target_id is None:
            payload = [{"ver": 0, "props": props}]
        else:
            payload = [{"subId": target_id, "ver": 0, "props": props}]

        upload_result = await self._vhome.async_data_upload(bridge_name, payload)
        if upload_result != 0:
            VLog.info(
                _TAG,
                f"[async_data_report][{upload_result}] target_id {target_id},"
                f"props:{props} failed to upload",
            )

    async def async_unregister_device_report(self):
        hass = self._bridge_entity.hass
        # if hass.config_entries
        if self.get_bridge_device_name() is None:
            VLog.warning(
                _TAG, "Don't report unregister device,bridge_device_name is None"
            )
            return

        unregister_devices = await self._bridge_entity.async_get_unregister_devices()
        VLog.info(_TAG, f"Report unregister devices number:{len(unregister_devices)}")
        payload = {}
        payload[VIVO_HA_CONF_ADDABLE_DEVS] = unregister_devices

        hass.bus.fire(
            EVENT_VHOME_DEV_STATE_CHANGE,
            {"data": payload, VIVO_DEVICE_NAME_CONFIG_KEY: None, "domain": DOMAIN},
        )

    async def async_remove_sub_devices(self):
        if self._bridge_entity is None:
            VLog.info(
                _TAG, f"[async_remove_sub_devices]: bridge has not initialized yet"
            )
            return
        if self._bridge_entity.config_entry is None:
            VLog.info(
                _TAG,
                f"[async_remove_sub_devices]: bridge.config_entry has not initialized yet",
            )
            return
        config_data = self._bridge_entity.config_entry.data
        if config_data is None:
            VLog.info(
                _TAG,
                f"[async_remove_sub_devices]: _bridge_entity.config_entry.data has not initialized yet",
            )
            return
        user_code = config_data.get(VIVO_BRIDGE_USER_CODE_CONFIG_KEY, None)
        device_name = config_data.get(VIVO_BRIDGE_DEVICE_NAME_CONFIG_KEY, None)
        mac = config_data.get(VIVO_BRIDGE_MAC_CONFIG_KEY, None)
        if user_code is None or device_name is None or mac is None:
            return
        result = await self._async_register_sub_devices(user_code, device_name, mac, [])
        VLog.info(_TAG, f"[async_remove_sub_devices] remove sub device result:{result}")

    async def async_binding_pending(
        self, method: int, bind_code: str, mac: str, timeout: int
    ):
        """
        Args:
        method(int): 0:mdns；1:QRCode
        bind_code (str):
        mac (str):
        timeout (int):
        Returns:
        None
        """
        if method == 1:
            # scan timout
            __DEFAULT_TIME_OUT = 300
            VLog.warning(_TAG, "Binding by QRCode")
        else:
            # mdns discovery
            __DEFAULT_TIME_OUT = 60
            VLog.warning(_TAG, "Binding by lan network")
        current_timestamp = time.time()
        timeout = timeout - 3
        if timeout <= 0:
            timeout = __DEFAULT_TIME_OUT - 3

        VLog.debug(_TAG, f"[async_binding_pending] start binding,timeout:{timeout}(s)")
        self._isbinding_pending = True
        while True:
            try:
                await asyncio.sleep(2)
            except asyncio.CancelledError:
                VLog.warning(_TAG, "[async_binding_pending] canceled")
                self._isbinding_pending = False
                break
            except Exception as e:
                VLog.warning(_TAG, f"[async_binding_pending] error:{e}")
                self._isbinding_pending = False
                break

            _current_timestamp = time.time()
            if _current_timestamp - current_timestamp > timeout:
                VLog.warning(_TAG, f"binding_pending timed out")
                self._isbinding_pending = False
                raise TimeoutError("timeout_abort")

            VLog.info(
                _TAG,
                f"[async_binding_pending]  bingcode:{bind_code} binding check in progress ",
            )
            bind_result_dict = await self._vhome.async_bind(bind_code, mac, GLOB_NAME)
            if bind_result_dict is None or len(bind_result_dict) == 0:
                VLog.info(
                    _TAG, f"[async_binding_pending] error bind_result_dict no data"
                )
                continue
            bind_result_code = bind_result_dict["code"]
            if bind_result_code == 10000:
                device_name = bind_result_dict["data"][VIVO_DEVICE_NAME_CONFIG_KEY]
                ip = bind_result_dict["data"]["ip"][0].split(":")
                host = ip[0]
                port = ip[1]
                cp_data = {
                    VIVO_BRIDGE_DEVICE_NAME_CONFIG_KEY: device_name,
                    VIVO_BRIDGE_HOST_CONFIG_KEY: host,
                    VIVO_BRIDGE_PORT_CONFIG_KEY: port,
                    VIVO_BRIDGE_USER_CODE_CONFIG_KEY: bind_code,
                    VIVO_BRIDGE_MAC_CONFIG_KEY: mac,
                }
                self._bridge_entity.hass.config_entries.async_update_entry(
                    self._bridge_entity.config_entry, data=cp_data
                )
                VLog.info(
                    _TAG,
                    f"[async_binding_pending] app bind successful bind_result_dict:{bind_result_dict}",
                )
                break

            VLog.info(_TAG, f"[async_binding_pending] error {bind_result_code}")
            continue

        await self.async_dm_service_start(self._bridge_entity.hass)
        self._isbinding_pending = False
        self.set_config_state(self.VConfig_STATE.STATE_INIT)
        return 0

    async def on_async_ui_select_device(self, entities: list):
        VLog.info(_TAG, f"[on_async_ui_select_device] user select device:{entities}")
        self._bridge_entity.hass.bus.async_fire(
            EVENT_VHOME_DEV_ADD, {"data": entities, "domain": DOMAIN}
        )

    def create_update_service(
        self, hass: HomeAssistant, device_name: str, mac: str, config_entry_id: str
    ):
        dev_reg = dr.async_get(hass)
        connection = (dr.CONNECTION_NETWORK_MAC, mac)
        identifier = (DOMAIN, config_entry_id, device_name)
        lib_version = self._vhome.version()
        build_time = self._vhome.build_time()
        try:
            self.get_bridge_entity().bridge_service = dev_reg.async_get_or_create(
                config_entry_id=config_entry_id,
                identifiers={identifier},
                connections={connection},
                manufacturer="",
                name=device_name,
                model="",
                entry_type=dr.DeviceEntryType.SERVICE,
                sw_version=f"{self.integration_version}-{lib_version}-{build_time}",
            )
            VLog.info(
                _TAG,
                f"[create_update_service][{device_name}] bridge_service:{self.get_bridge_entity().bridge_service}",
            )
            VLog.info(
                _TAG,
                f"uuid:{list(self.get_bridge_entity().bridge_service.identifiers)[0][2]}",
            )
            VLog.info(_TAG, f"id  :{self.get_bridge_entity().bridge_service.id}")

            if self.get_bridge_entity().bridge_service.disabled_by:
                self._bridge_entity.set_device_enable(False)
            else:
                self._bridge_entity.set_device_enable(True)
            if (
                self._cancel_listen_device_registry_updated_dict.get(
                    self.get_bridge_entity().bridge_service.id
                )
                is None
            ):
                VLog.info(
                    _TAG,
                    f"[create_update_service] "
                    f"add {device_name} {self.get_bridge_entity().bridge_service.id} device listener",
                )
                self._cancel_listen_device_registry_updated_dict[
                    self.get_bridge_entity().bridge_service.id
                ] = async_track_device_registry_updated_event(
                    self._bridge_entity.hass,
                    self.get_bridge_entity().bridge_service.id,
                    self._async_device_availability_update_event,
                    job_type=HassJobType.Coroutinefunction,
                )
            else:
                VLog.info(
                    _TAG,
                    f"[set_config_devices] {device_name} device listener already exists",
                )

        except Exception as e:
            VLog.error(
                _TAG,
                f"[create_update_service][async_get_or_create] error linking device: {e}",
            )

    async def async_bridge_remove(self):
        if self._bridge_entity is None:
            VLog.info(_TAG, f"[async_bridge_remove]：bridge has not initialized yet")
            return
        VLog.info(_TAG, "[async_bridge_remove] remove ... ...")
        bridge_service = self._bridge_entity.bridge_service
        
        if bridge_service is not None :
            if bridge_service.id is not None:
                VLog.info(_TAG,
                          f"[async_bridge_remove] remove service:{self.get_bridge_entity().bridge_service.id}")
                dev_reg = dr.async_get(self.get_bridge_entity().hass)
                dev_reg.async_remove_device(
                        self.get_bridge_entity().bridge_service.id
                    )

        await self._bridge_entity.bridge_config_handle.async_remove()
        self._bridge_entity.bridge_config_data.clear()
        await self._bridge_entity.bridge_config_handle.async_save(
            self._bridge_entity.bridge_config_data
        )

    def get_bridge_entity(self) -> VBridgeEntity | None:
        return self._bridge_entity

    def get_vhome(self) -> VHome:
        return self._vhome

    def get_local_server(self) -> VLocalService:
        return self._local_server

    def get_bridge_device_name(self) -> str | None:
        if self._bridge_entity is None:
            return None
        if self._bridge_entity.config_entry.data is None:
            return None
        return self._bridge_entity.config_entry.data.get(
            VIVO_BRIDGE_DEVICE_NAME_CONFIG_KEY, None
        )

    def get_bridge_mac(self) -> str | None:
        if self._bridge_entity is None:
            return None
        if self._bridge_entity.config_entry.data is None:
            return None
        if VIVO_BRIDGE_MAC_CONFIG_KEY not in self._bridge_entity.config_entry.data:
            return None
        return self._bridge_entity.config_entry.data.get(
            VIVO_BRIDGE_MAC_CONFIG_KEY, None
        )

    def get_bridge_device(self) -> VBridgeDevice | None:
        if self._bridge_entity is None:
            return None
        if self._bridge_entity.config_entry.data is None:
            return None
        return VBridgeDevice(
            self._bridge_entity.config_entry.data.get(
                VIVO_BRIDGE_DEVICE_NAME_CONFIG_KEY, None
            ),
            self._bridge_entity.config_entry.data.get(VIVO_BRIDGE_MAC_CONFIG_KEY, None),
            self._bridge_entity.config_entry.data.get(
                VIVO_BRIDGE_HOST_CONFIG_KEY, None
            ),
            self._bridge_entity.config_entry.data.get(
                VIVO_BRIDGE_PORT_CONFIG_KEY, None
            ),
            self._bridge_entity.config_entry.data.get(
                VIVO_BRIDGE_USER_CODE_CONFIG_KEY, None
            ),
        )

    async def uninstall(self):
        VLog.info(_TAG, "[uninstall] ...")
        self._integration_enable = False
        if (
            self.get_bridge_device_name() is not None
            and len(self.get_bridge_device_name()) > 0
        ):
            VLog.info(_TAG, "[async_disconnect]...")
            await self._vhome.async_disconnect(self.get_bridge_device_name())
        self.cancel_bcode_task()
        await self._un_register_listener()
        await self._reconnector.stop_reconnect("uninstall")

    def get_device_list(self, config_entry: ConfigEntry) -> list[Any]:
        return config_entry.data.get(VIVO_HA_CONFIG_DATA_DEVICES_KEY, [])

    """ private method begin"""

    def _register_events_listener(self, hass):
        self._cancel_listen_entity_registry_updated = hass.bus.async_listen(
            EVENT_ENTITY_REGISTRY_UPDATED, self._entity_registry_updated_event
        )
        self._cancel_listen_delete_device = hass.bus.async_listen(
            EVENT_VHOME_DEV_DEL, self._async_handle_delete_device_event
        )
        # control event
        self._cancel_listen_set_status = hass.bus.async_listen(
            EVENT_VHOME_DEV_SET_STATUS, self._async_handle_set_status_event
        )
        # unbind bridge event for local
        self._cancel_listen_bridge_remove = hass.bus.async_listen(
            EVENT_VHOME_DEV_REMOVE_BRIDGE, self._async_handle_remove_bridge_event
        )
        # sub device register result event
        self._cancel_listen_dev_reg = hass.bus.async_listen(
            EVENT_VHOME_DEV_REG_RESULT, self._async_handle_dev_reg_result
        )
        self._cancel_listen_dev_unreg = hass.bus.async_listen(
            EVENT_VHOME_DEV_UNREG_RESULT, self._async_handle_dev_unreg_result
        )
        # add sub devices event
        self._cancel_listen_add_device = hass.bus.async_listen(
            EVENT_VHOME_DEV_ADD, self._async_handle_add_device_event
        )
        self._cancel_listen_state_change = hass.bus.async_listen(
            EVENT_VHOME_DEV_STATE_CHANGE, self._async_handle_state_change_event
        )
        self._cancel_listen_state_flush = hass.bus.async_listen(
            EVENT_VHOME_DEV_STATE_FLUSH, self._async_handle_state_flush_event
        )
        # update bridge online state event
        self._cancel_listen_bridge_online = hass.bus.async_listen(
            EVEVT_VHOME_BRIDGE_ONLINE, self._async_handle_bridge_online_event
        )
        # reconnect event
        self._cancel_listen_reconnect = hass.bus.async_listen(
            EVENT_VHOME_RECONNECT, self._async_handle_reconnect_event
        )

    async def _un_register_listener(self):
        try:
            if (
                self._cancel_ha_state_changed_listener_dict is not None
                and len(self._cancel_ha_state_changed_listener_dict) > 0
            ):
                VLog.info(
                    _TAG,
                    f"[un_register_listener] cancel state listener list size "
                    f"{len(self._cancel_ha_state_changed_listener_dict)}",
                )
                for (
                    listener_id,
                    listener_value,
                ) in self._cancel_ha_state_changed_listener_dict.items():
                    if listener_value is not None and callable(listener_value):
                        VLog.info(
                            _TAG,
                            f"[un_register_listener] cancel entity listen {listener_id}",
                        )
                        listener_value()
                self._cancel_ha_state_changed_listener_dict = {}
            if (
                self._cancel_listen_device_registry_updated_dict is not None
                and len(self._cancel_listen_device_registry_updated_dict) > 0
            ):
                VLog.info(
                    _TAG,
                    f"[un_register_listener] cancel device listener list size "
                    f"{len(self._cancel_listen_device_registry_updated_dict)}",
                )
                for (
                    listener_id,
                    listener_value,
                ) in self._cancel_listen_device_registry_updated_dict.items():
                    if listener_value is not None and callable(listener_value):
                        VLog.info(
                            _TAG,
                            f"[un_register_listener] cancel device listen {listener_id}",
                        )
                        listener_value()
                self._cancel_listen_device_registry_updated_dict = {}
            if self._cancel_listen_reconnect is not None and callable(
                self._cancel_listen_reconnect
            ):
                VLog.info(_TAG, "[un_register_listener] cancel listen reconnect")
                self._cancel_listen_reconnect()
                self._cancel_listen_reconnect = None
            if self._cancel_listen_bridge_online is not None and callable(
                self._cancel_listen_bridge_online
            ):
                VLog.info(_TAG, "[un_register_listener] cancel listen bridge online")
                self._cancel_listen_bridge_online()
                self._cancel_listen_bridge_online = None
            if self._cancel_listen_state_flush is not None and callable(
                self._cancel_listen_state_flush
            ):
                VLog.info(_TAG, "[un_register_listener] cancel listen State Flush")
                self._cancel_listen_state_flush()
                self._cancel_listen_state_flush = None
            if self._cancel_listen_state_change is not None and callable(
                self._cancel_listen_state_change
            ):
                VLog.info(_TAG, "[un_register_listener] cancel Listen State Change")
                self._cancel_listen_state_change()
                self._cancel_listen_state_change = None
            if self._cancel_listen_add_device is not None and callable(
                self._cancel_listen_add_device
            ):
                VLog.info(_TAG, "[un_register_listener] cancel Listen Add Device")
                self._cancel_listen_add_device()
                self._cancel_listen_add_device = None
            if self._cancel_listen_dev_unreg is not None and callable(
                self._cancel_listen_dev_unreg
            ):
                VLog.info(_TAG, "[un_register_listener] cancel Listen dev unreg")
                self._cancel_listen_dev_unreg()
                self._cancel_listen_dev_unreg = None
            if self._cancel_listen_dev_reg is not None and callable(
                self._cancel_listen_dev_reg
            ):
                VLog.info(_TAG, "[un_register_listener] cancel Listen dev reg")
                self._cancel_listen_dev_reg()
                self._cancel_listen_dev_reg = None
            if self._cancel_listen_bridge_remove is not None and callable(
                self._cancel_listen_bridge_remove
            ):
                VLog.info(_TAG, "[un_register_listener] cancel Listen bridge remove")
                self._cancel_listen_bridge_remove()
                self._cancel_listen_bridge_remove = None
            if self._cancel_listen_set_status is not None and callable(
                self._cancel_listen_set_status
            ):
                VLog.info(_TAG, "[un_register_listener] cancel Listen set status")
                self._cancel_listen_set_status()
                self._cancel_listen_set_status = None
            if self._cancel_listen_entity_registry_updated is not None and callable(
                self._cancel_listen_entity_registry_updated
            ):
                VLog.info(_TAG, "[un_register_listener] cancel entity registry updated")
                self._cancel_listen_entity_registry_updated()
                self._cancel_listen_entity_registry_updated = None
            if self._cancel_listen_delete_device is not None and callable(
                self._cancel_listen_delete_device
            ):
                VLog.info(_TAG, "[un_register_listener] cancel Listen delete Device")
                self._cancel_listen_delete_device()
                self._cancel_listen_delete_device = None
        except Exception as e:
            VLog.warning(
                _TAG, "[un_register_listener] cancel_listen has exception:" + str(e)
            )

    def _sub_devices_registered_is_update(self, mac_id_list: list):
        if len(mac_id_list) != len(self._registered_device_mac_list):
            return True
        for mac_id in mac_id_list:
            if mac_id not in self._registered_device_mac_list:
                return True
        return False

    async def _async_sync_sub_devices(self, config_entry, device_list):
        entity_ids = [device["entity_id"] for device in device_list]
        sub_devices: list[dict] = []
        for entity_id in entity_ids:
            VLog.info(_TAG, f"[_async_sync_sub_devices] sub_device:{entity_id}")
            try:
                node = VModel(self._bridge_entity.hass, config_entry, entity_id)
                if node.model != {}:
                    sub_devices.append(node.model)
            except Exception as e:
                VLog.warning(
                    _TAG,
                    f"[async_sync_sub_devices] vModel instantiation failed,ignore sync device {e}",
                )
                return
        VLog.info(
            _TAG, f"[async_sync_sub_devices] sub_devices:{json.dumps(sub_devices)}"
        )
        if len(sub_devices) >= 0:
            user_code = config_entry.data.get(VIVO_BRIDGE_USER_CODE_CONFIG_KEY, None)
            device_name = config_entry.data.get(
                VIVO_BRIDGE_DEVICE_NAME_CONFIG_KEY, None
            )
            mac = config_entry.data.get(VIVO_BRIDGE_MAC_CONFIG_KEY, None)
            result = await self._async_register_sub_devices(
                user_code, device_name, mac, sub_devices
            )
            VLog.info(_TAG, f"[async_sync_sub_devices] register result:{result}")

    def _on_vhome_state_changed_callback(self, data: dict) -> None:
        """
        bridge state changed callback
        {"state": 0, "payload": {"connect_result": 0}}
        """
        VLog.info(
            _TAG,
            f"[state changed] {json.dumps(data)},the bridge enable is {self._integration_enable}",
        )
        if data is None:
            return
        if self._bridge_entity is None:
            VLog.info(_TAG, f"[state changed] bridge has not initialized yet")
            return
        # state is connect established
        if data.get("state") == 0:
            self.get_bridge_entity().hass.bus.fire(EVEVT_VHOME_BRIDGE_ONLINE, {})
        elif data.get("state") == 1:
            reason_code = data.get("payload", {}).get("connect_result", -99)
            # bridge has been removed by other client,and it has been removed in server
            if reason_code == self.__BRIDGE_DEVICE_REMOVED_CODE:
                self.get_bridge_entity().hass.bus.fire(
                    EVENT_VHOME_DEV_REMOVE_BRIDGE, {}
                )
            else:
                if self._bridge_entity.get_device_enable() is False:
                    VLog.info(
                        _TAG,
                        f"[state changed] bridge device is disable,not post reconnect event",
                    )
                    return
                if self._integration_enable:
                    bridge_device = DeviceManager.instance().get_bridge_device()
                    event_data = {
                        VIVO_BRIDGE_HOST_CONFIG_KEY: bridge_device.host,
                        VIVO_BRIDGE_PORT_CONFIG_KEY: bridge_device.port,
                        VIVO_BRIDGE_DEVICE_NAME_CONFIG_KEY: bridge_device.name,
                        VIVO_BRIDGE_USER_CODE_CONFIG_KEY: bridge_device.user_code,
                        "reason": "offline",
                    }
                    if (
                        bridge_device.host is None
                        or bridge_device.port is None
                        or bridge_device.name is None
                        or bridge_device.user_code is None
                    ):
                        VLog.debug(_TAG, "bridge_device data is not useful")
                        return

                    self.get_bridge_entity().hass.bus.fire(
                        EVENT_VHOME_RECONNECT, event_data
                    )
                else:
                    VLog.info(
                        _TAG,
                        f"[state changed] bridge is disable,not post reconnect event",
                    )
        else:
            VLog.info(_TAG, f"[state changed]：unknown state:{json.dumps(data)}")

    def _on_vhome_data_received_callback(self, data: dict) -> None:
        VLog.info(_TAG, f"[data received]：{json.dumps(data)}")
        if data is None or not isinstance(data, dict) or "payload" not in data:
            return
        if self._bridge_entity is None:
            VLog.info(_TAG, f"[data received]：bridge has not initialized yet")
            return
        action_type = data.get("payload").get("act")
        payload_body_data_list = data.get("payload").get("body")
        if (
            payload_body_data_list is None
            or not isinstance(payload_body_data_list, list)
            or len(payload_body_data_list) == 0
        ):
            VLog.warning(_TAG, f"[data received]：action data is empty")
            return
        if action_type == "set":
            self._on_vhome_set_action_callback(payload_body_data_list)
        elif action_type == "event":
            self._on_vhome_event_action_callback(payload_body_data_list)
        else:
            VLog.info(_TAG, f"[data received]：not support action:{action_type}")

    def _on_vhome_set_action_callback(self, payload_body_data_list: list):
        VLog.info(_TAG, f"[set_action]:{payload_body_data_list}")
        if self._bridge_entity is None:
            VLog.info(_TAG, f"[set_action] bridge has not initialized yet")
            return
        if self._bridge_entity.get_device_enable() is False:
            VLog.info(_TAG, f"[set_action] bridge device is disable")
            return
        for payload_body_item in payload_body_data_list:
            props_dict = payload_body_item.get("props")
            if props_dict is None or len(props_dict) == 0:
                continue
            """control sub device"""
            sub_device_id = payload_body_item.get("subId")
            if sub_device_id is None or len(sub_device_id) == 0:
                device_control = {"props": props_dict}
            else:
                device_control = {"deviceName": sub_device_id, "props": props_dict}

            self.get_bridge_entity().hass.bus.fire(
                EVENT_VHOME_DEV_SET_STATUS, device_control
            )

    def _on_vhome_event_action_callback(self, payload_body_data_list: list):
        unregister_sub_device_list_of_dicts: list[dict[str, str]] = []
        if self._bridge_entity is None:
            VLog.info(_TAG, f"[event_action]：bridge has not initialized yet")
            return

        for payload_body_item in payload_body_data_list:
            props_dict = payload_body_item.get("props")
            if props_dict is None or len(props_dict) == 0:
                continue
            is_unbind_event = False
            is_unbind_data = props_dict.get("unbind")
            if is_unbind_data is not None and is_unbind_data == 1:
                is_unbind_event = True
            if is_unbind_event:
                sub_device_id = payload_body_item.get("subId")
                if sub_device_id is not None:
                    """unbind sub device"""
                    unregister_sub_device_list_of_dicts.append(
                        {VIVO_BRIDGE_DEVICE_ID_CLOUD_KEY: sub_device_id}
                    )
                else:
                    """unbind bridge"""
                    self.get_bridge_entity().hass.bus.fire(
                        EVENT_VHOME_DEV_REMOVE_BRIDGE, {}
                    )
                    # 网桥被解绑，直接忽略掉子设备的解绑逻辑；
                    VLog.warning(_TAG, "VHome Bridge is unbind by user!!!")
                    return

        if (
            unregister_sub_device_list_of_dicts is not None
            and len(unregister_sub_device_list_of_dicts) > 0
        ):
            self.get_bridge_entity().hass.bus.fire(
                EVENT_VHOME_DEV_UNREG_RESULT,
                {"success": unregister_sub_device_list_of_dicts},
            )

    def _on_vhome_local_event_callback(self, data: dict):
        async def _handle_bcode_async(data):
            try:
                VLog.info(_TAG, "[_handle_bcode_async] start")
                bind_code: str = None
                _delay_time: int = 300
                errors: dict[str, str] = {}
                description_placeholders: {} = {}
                mac: str = self.get_bridge_device().mac

                bcode_dict_result = await self._vhome.async_get_bcode(mac)
                VLog.info(
                    _TAG,
                    f"[_handle_bcode_async] bcode_dict_result:{bcode_dict_result}",
                )
                if bcode_dict_result is None or bcode_dict_result.get("data") is None:
                    errors["base"] = "network_error"
                elif bcode_dict_result.get("code") == 10000:
                    bcode_dict_data = bcode_dict_result.get("data")
                    bind_code = bcode_dict_data.get(VIVO_HA_CONF_BIND_CODE)
                    _delay_time = bcode_dict_data.get("expireIn")
                    if bind_code is None or bind_code == "":
                        VLog.warning(
                            _TAG,
                            f"[async_get_bcode] bind_code is empty {bcode_dict_result}",
                        )
                        errors["base"] = "network_error"
                    else:
                        VLog.debug(_TAG, f"[async_get_bcode] bind_code:{bind_code}")
                else:
                    VLog.warning(_TAG, f"[async_get_bcode] failed {bcode_dict_result}")
                    code = bcode_dict_result.get("code")
                    errors["base"] = "network_error"

                if bind_code is None:
                    VLog.warning(_TAG, f"[async_get_bcode] failed {bcode_dict_result}")
                else:
                    bcode_payload: dict = {"code": bind_code}
                    await self._vhome.async_send_bind_code_to_app(bcode_payload)
                    await self.async_binding_pending(0, bind_code, mac, _delay_time)
            except asyncio.CancelledError:
                VLog.warning(_TAG, "[_handle_bcode_async] canceled")
                return
            except Exception as e:
                VLog.warning(_TAG, f"[_handle_bcode_async] error:{e}")
                return

        if "payload" not in data:
            return

        if data.get("payload", {}).get("cmd") == 0:
            VLog.info(_TAG, "握手成功，准备去获取bcode.")
            self.set_config_state(self.VConfig_STATE.STATE_LAN)
            self.cancel_bcode_task()

            def schedule():
                self._bcode_task = asyncio.create_task(_handle_bcode_async(data))

            self._bridge_entity.hass.loop.call_soon_threadsafe(schedule)

        elif data.get("payload", {}).get("cmd") == 1:
            # 客户端断开，要停止bcode处理逻辑
            VLog.info(_TAG, "客户端断开... ...")
            if self._isbinding_pending is False:
                self.cancel_bcode_task()
        else:
            return

    def cancel_bcode_task(self):
        if self._bcode_task and not self._bcode_task.done():
            self._bcode_task.cancel()
            VLog.info(_TAG, "bcode task canceled.")
        else:
            VLog.info(_TAG, "bcode task already canceled.")

    async def _async_handle_delete_device_event(self, event):
        """删除服务端数据，不需要再刷新和清除本地数据，上文已处理"""
        if self._bridge_entity is None:
            VLog.info(_TAG, f"[delete_device_event]：bridge has not initialized yet")
            return
        data = event.data
        if not data:
            return
        VLog.info(_TAG, f"[delete_device_event]：{data}")
        entity_ids = data.get("entity_ids", [])
        if not entity_ids:
            return

        config_data = self._bridge_entity.config_entry.data
        user_code = config_data.get(VIVO_BRIDGE_USER_CODE_CONFIG_KEY, None)
        device_name = config_data.get(VIVO_BRIDGE_DEVICE_NAME_CONFIG_KEY, None)
        mac = config_data.get(VIVO_BRIDGE_MAC_CONFIG_KEY, None)
        remain_entity_ids = Utils.get_entity_ids(self._bridge_entity.bridge_config_data)
        VLog.info(_TAG, f"[delete_device_event] remain device:{remain_entity_ids}")
        sub_devices: list = []
        for entity_id in remain_entity_ids:
            node = VModel(
                self._bridge_entity.hass, self._bridge_entity.config_entry, entity_id
            )
            if node.model != {}:
                logic_mac = node.model.get(VIVO_HA_KEY_WORLD_DEV_LOGIC_MAC, None)
                if logic_mac is None:
                    continue
                sub_devices.append(node.model)
        reg_result = await self._async_register_sub_devices(
            user_code, device_name, mac, sub_devices
        )
        VLog.info(_TAG, f"[delete_device_event]：delete result {reg_result}")

    def create_delay_job(self, hass: HomeAssistant, delay, func):
        @callback
        def _run(now):
            self._delayed_job = None
            try:
                func()
            except Exception as e:
                VLog.error(_TAG, "Delay job error:%s", e)

        if self._delayed_job:
            self._delayed_job()
        self._delayed_job = async_call_later(hass, delay, _run)

    def delayed_job_fun(self):
        VLog.info(_TAG, "delayed_job_handle :实体变化后的最终执行函数！")

        def schedule():
            self._bcode_task = asyncio.create_task(
                self.async_unregister_device_report()
            )

        self._bridge_entity.hass.loop.call_soon_threadsafe(schedule)

    async def _entity_registry_updated_event(self, event):
        if self._bridge_entity is None:
            VLog.info(_TAG, f"[registry_updated_event]：bridge has not initialized yet")
            return
        data = event.data
        if not data:
            return
        VLog.info(_TAG, f"_entity_registry_updated_event data :{data}")
        if (
            data.get("action") == "update"
            and "changes" in data
            and "disabled_by" in data["changes"]
        ):
            entity_id = data.get(ATTR_ENTITY_ID)
            logicMac = Utils.get_logic_mac_by_entity_id(
                entity_id, self._bridge_entity.bridge_config_data
            )
            VLog.info(_TAG, f"logicMac:{logicMac}")
            if logicMac is None:
                return
            disabled_by = data["changes"].get("disabled_by", {})
            if disabled_by == {}:
                return
            elif disabled_by is None:
                VLog.warning(_TAG, f"Disable entity_id={entity_id}")
                await self._async_device_enable_event(logicMac, False)
            else:
                VLog.warning(_TAG, f"Enable entity_id={entity_id}")
                await self._async_device_enable_event(logicMac, True)
        elif data.get("action") == "create":
            self.create_delay_job(self._bridge_entity.hass, 2, self.delayed_job_fun)
        elif data.get("action") == "remove":
            self.create_delay_job(self._bridge_entity.hass, 2, self.delayed_job_fun)
            entity_id = data.get(ATTR_ENTITY_ID)
            entry_id_obtain = Utils.get_entry_id_from_entity_id(
                entity_id, self._bridge_entity.bridge_config_data
            )
            if not entry_id_obtain:
                return
            VLog.info(
                _TAG, f"[registry_updated_remove]：remove {entity_id} {entry_id_obtain}"
            )
            integration_config_entries = (
                self._bridge_entity.hass.config_entries.async_entries()
            )
            integration_config_entry = next(
                (
                    entry
                    for entry in integration_config_entries
                    if entry.entry_id == entry_id_obtain
                ),
                None,
            )
            if integration_config_entry is None:
                entity_ids = Utils.get_entity_ids_from_entry_id(
                    entry_id_obtain, self._bridge_entity.bridge_config_data
                )
                if not entity_ids:
                    return
                reason = "remove_entry_3rd"
                event_data = {"entity_ids": entity_ids, "action": "remove_entry_3rd"}
                VLog.info(
                    _TAG,
                    f"[registry_updated_remove]：remove entry {entry_id_obtain} {entity_ids}",
                )
            else:
                entity_ids = [entity_id]
                if not entity_ids:
                    return
                reason = "remove_entity_3rd"
                event_data = {"entity_ids": entity_ids, "action": "remove_entity_3rd"}
                VLog.info(
                    _TAG, f"[registry_updated_remove]：remove entity {entity_ids}"
                )
            VLog.info(
                _TAG,
                f"[registry_updated_remove]：before remove {entity_ids} "
                f"\n\t {self._bridge_entity.bridge_config_data}",
            )
            self._bridge_entity.bridge_config_data = [
                item
                for item in self._bridge_entity.bridge_config_data
                if item[VIVO_DEVICE_ENTITY_ID_KEY] not in entity_ids
            ]
            existing_entity_ids = {
                item[VIVO_DEVICE_ENTITY_ID_KEY]
                for item in self._bridge_entity.bridge_config_data
            }
            existing_mac_ids = {
                item[VIVO_HA_KEY_WORLD_DEV_LOGIC_MAC]
                for item in self._bridge_entity.bridge_config_data
            }
            await self._async_update_cache_for_unregister(
                existing_entity_ids, existing_mac_ids
            )
            VLog.info(
                _TAG,
                f"[registry_updated_remove]:after {reason} {entity_ids} "
                f"\n\t data is {self._bridge_entity.bridge_config_data}",
            )
            await self._bridge_entity.bridge_config_handle.async_remove()
            await self._bridge_entity.bridge_config_handle.async_save(
                self._bridge_entity.bridge_config_data
            )
            await self._async_set_config_devices(reason)
            self.get_bridge_entity().hass.bus.fire(EVENT_VHOME_DEV_DEL, event_data)

    async def _async_handle_set_status_event(self, event):
        if self._bridge_entity is None:
            VLog.info(_TAG, f"[set_status]：bridge has not initialized yet")
            return

        data = event.data
        VLog.info(_TAG, f"[set_status]：{data}")
        device_name = data.get("deviceName")
        props = data.get("props")
        if device_name is None:
            add_entity_ids = []
            if VIVO_HA_CONF_ADDABLE_DEVS not in props:
                return
            addable_devices = props.get(VIVO_HA_CONF_ADDABLE_DEVS, [])
            if len(addable_devices) == 0:
                return
            for item in addable_devices:
                entity_obj_id = item.split(".")[0]
                e_id = await Utils.get_entity_id_from_registry_id(
                    self.get_bridge_entity().hass, entity_obj_id
                )
                if e_id is not None:
                    add_entity_ids.append(e_id)
                    VLog.debug(_TAG, f"{entity_obj_id}={e_id}")

            options_source_list = await self.get_bridge_entity().get_supported_list()
            entity_ids = [
                option[ATTR_ENTITY_ID]
                for option in options_source_list
                if option[ATTR_ENTITY_ID] in add_entity_ids
            ]
            # 默认勾选已选择的列表
            config_devices = self._bridge_entity.config_entry.data.get(
                VIVO_HA_CONFIG_DATA_DEVICES_KEY
            )
            default_selected_entity_id_list = []
            if config_devices is not None and len(config_devices) > 0:
                default_selected_entity_id_list = [
                    config_device_item[ATTR_ENTITY_ID]
                    for config_device_item in config_devices
                ]
                VLog.debug(
                    _TAG,
                    "[set_status]:default_selected_entity_id_list={}".format(
                        json.dumps(default_selected_entity_id_list)
                    ),
                )
            VLog.debug(
                _TAG,
                "[set_status]:user add entity_ids={}".format(json.dumps(entity_ids)),
            )
            await self.on_async_ui_select_device(
                entity_ids + default_selected_entity_id_list
            )
        else:
            await self._bridge_entity.async_sub_dev_attributes_set(device_name, props)

    async def _async_handle_remove_bridge_event(self, event):
        if self._bridge_entity is None:
            VLog.info(_TAG, f"[remove_bridge]：bridge has not initialized yet")
            return
        entity_id = self._bridge_entity.config_entry.entry_id
        VLog.warning(
            _TAG, "Remove vHome Bridge Service,and Re-running the integration."
        )
        cp_data = {
            VIVO_BRIDGE_MAC_CONFIG_KEY: self._bridge_entity.config_entry.data.get(
                VIVO_BRIDGE_MAC_CONFIG_KEY, None
            )
        }
        await self._vhome.async_disconnect(self.get_bridge_device_name())
        self._bridge_entity.hass.config_entries.async_update_entry(
            self._bridge_entity.config_entry, data=cp_data
        )
        await self.async_bridge_remove()
        await self._bridge_entity.hass.config_entries.async_reload(entity_id)

    async def _async_handle_dev_reg_result(self, event):
        VLog.info(_TAG, f"[async_handle_dev_reg_result] event:{event}")
        if self._bridge_entity is None:
            VLog.info(
                _TAG, f"[async_handle_dev_reg_result]：bridge has not initialized yet"
            )
            return
        event_data = event.data
        if event_data is None or len(event_data) == 0:
            return
        success_devs = event_data.get("success", [])
        # 使用dn过滤，dn的唯一性更合适
        success_dns = [entry[VIVO_DEVICE_NAME_CONFIG_KEY] for entry in success_devs]
        VLog.info(
            _TAG,
            f"[async_handle_dev_reg_result] success_dns:{success_dns} success_devs {success_devs}",
        )
        # 在已经保存的设备中，去掉本次注册成功的设备。
        self._bridge_entity.bridge_config_data = [
            item
            for item in self._bridge_entity.bridge_config_data
            if item[VIVO_DEVICE_NAME_CONFIG_KEY] not in success_dns
        ]
        # 确保现在保存的配置文件数据为之前成功本次也成功的数据；
        new_device_list = []
        for success_dev in success_devs:
            new_obj = {}
            logic_mac: str = success_dev[VIVO_HA_KEY_WORLD_DEV_LOGIC_MAC]
            platform: str = logic_mac.split(".")[1]
            if platform not in VIVO_HA_PLATFORM_SUPPORT_LIST:
                VLog.warning(
                    _TAG,
                    f"[async_handle_dev_reg_result]you select device platform is {platform} "
                    f"not support now!!!",
                )
                continue
            entity_id = success_dev[VIVO_DEVICE_ENTITY_ID_KEY]
            VLog.info(_TAG, f"[async_handle_dev_reg_result]entity_id:{entity_id}")
            _vModel = VModel(
                self._bridge_entity.hass, self._bridge_entity.config_entry, entity_id
            )
            if _vModel is None:
                continue
            dev_model = _vModel.model
            if dev_model is None or len(dev_model) == 0:
                continue
            new_obj[VIVO_HA_KEY_WORLD_DEV_LOGIC_MAC] = success_dev[
                VIVO_HA_KEY_WORLD_DEV_LOGIC_MAC
            ]
            new_obj[VIVO_DEVICE_NAME_CONFIG_KEY] = success_dev[
                VIVO_DEVICE_NAME_CONFIG_KEY
            ]
            new_obj[VIVO_DEVICE_ENTITY_ID_KEY] = entity_id
            new_obj[ATTR_FRIENDLY_NAME] = _vModel.entity_attributes[ATTR_FRIENDLY_NAME]
            new_obj[VIVO_HA_KEY_WORLD_DEV_ENTRY_ID] = _vModel.entity_obj.config_entry_id
            new_device_list.append(new_obj.copy())
            VLog.info(
                _TAG,
                f"[async_handle_dev_reg_result][{entity_id}]add dev_model:{dev_model}",
            )
            self._bridge_entity.bridge_config_data.append(new_obj.copy())
            if self._cancel_ha_state_changed_listener_dict.get(entity_id) is None:
                VLog.info(
                    _TAG,
                    f"[async_handle_dev_reg_result] {entity_id} add state change listener",
                )
                cancel_listen_state_change = async_track_state_change_event(
                    self._bridge_entity.hass,
                    entity_id,
                    self._bridge_entity.async_handle_entity_state_change,
                    job_type=HassJobType.Coroutinefunction,
                )
                self._cancel_ha_state_changed_listener_dict[entity_id] = (
                    cancel_listen_state_change
                )
            else:
                VLog.info(
                    _TAG,
                    f"[async_handle_dev_reg_result] {entity_id} state change listener already exists",
                )

        await self._bridge_entity.bridge_config_handle.async_remove()
        await self._bridge_entity.bridge_config_handle.async_save(
            self._bridge_entity.bridge_config_data
        )
        self._bridge_entity.bridge_config_data = (
            await self._bridge_entity.bridge_config_handle.async_load() or []
        )
        await self._async_set_config_devices("register")
        await self._async_fill_in_device_id_to_config_date()
        if len(new_device_list) > 0:
            self._bridge_entity.hass.bus.async_fire(
                EVENT_VHOME_DEV_STATE_FLUSH,
                {"devices": new_device_list, "domain": DOMAIN},
            )
            await self.async_unregister_device_report()

    def _async_device_entries_for_config_entry(
        self, registry: dr.DeviceRegistry, config_entry_id: str
    ) -> (list)[DeviceEntry]:
        return [
            device
            for device in registry.devices.values()
            if config_entry_id in device.config_entries
            and device.entry_type is not dr.DeviceEntryType.SERVICE
        ]

    async def _async_fill_in_device_id_to_config_date(self):
        if self._bridge_entity is None:
            VLog.info(
                _TAG,
                f"[async_fill_in_device_id_to_config_date]：bridge has not initialized yet",
            )
            return
        self._bridge_entity.bridge_config_data = [
            item for item in self._bridge_entity.bridge_config_data
        ]
        if not self._bridge_entity.bridge_config_data:
            return
        dev_reg = dr.async_get(self._bridge_entity.hass)
        reg_devices = self._async_device_entries_for_config_entry(
            dev_reg, self._bridge_entity.config_entry.entry_id
        )
        if not reg_devices:
            VLog.info(
                _TAG, f"[async_fill_in_device_id_to_config_date] reg_devices is empty"
            )
            return
        devices_dict = {
            list(device.identifiers)[0][2]: device.id for device in reg_devices
        }
        for item in self._bridge_entity.bridge_config_data:
            logic_mac = item.get(VIVO_HA_KEY_WORLD_DEV_LOGIC_MAC, "")
            if logic_mac in devices_dict:
                item[VIVO_DEVICE_ID_KEY] = devices_dict[logic_mac]
        VLog.info(
            _TAG,
            f"[async_fill_in_device_id_to_config_date] "
            f"devices:{self._bridge_entity.bridge_config_data}",
        )
        await self._bridge_entity.bridge_config_handle.async_remove()
        await self._bridge_entity.bridge_config_handle.async_save(
            self._bridge_entity.bridge_config_data
        )
        self._bridge_entity.bridge_config_data = (
            await self._bridge_entity.bridge_config_handle.async_load() or []
        )

    async def _async_handle_dev_unreg_result(self, event):
        if self._bridge_entity is None:
            VLog.info(
                _TAG, f"[async_handle_dev_unreg_resul]：bridge has not initialized yet"
            )
            return
        event_data = event.data
        if event_data is None or len(event_data) == 0:
            return
        success_devs = event_data.get("success")
        VLog.info(_TAG, f"[async_handle_dev_unreg_result] remove devs:{success_devs}")
        """ [{"logicMac":""}] from user select or [{"deviceName":""} from cloud"""
        if success_devs is None or len(success_devs) == 0:
            VLog.info(_TAG, f"[async_handle_dev_unreg_result] no data:{event}")
            return
        success_ids = [
            success_dev_item.get(VIVO_HA_KEY_WORLD_DEV_LOGIC_MAC)
            for success_dev_item in success_devs
            if success_dev_item.get(VIVO_HA_KEY_WORLD_DEV_LOGIC_MAC) is not None
        ]
        if len(success_ids) > 0:
            """exclude the logicMac in success_ids from bridge_config_data,then save them"""
            self._bridge_entity.bridge_config_data = [
                item1
                for item1 in self._bridge_entity.bridge_config_data
                if item1[VIVO_HA_KEY_WORLD_DEV_LOGIC_MAC] not in success_ids
            ]
        else:
            """parse deviceName """
            success_ids = [
                success_dev_item.get(VIVO_BRIDGE_DEVICE_ID_CLOUD_KEY)
                for success_dev_item in success_devs
                if success_dev_item.get(VIVO_BRIDGE_DEVICE_ID_CLOUD_KEY) is not None
            ]
            if len(success_ids) > 0:
                """exclude the dn in success_ids from bridge_config_data,then save them"""
                self._bridge_entity.bridge_config_data = [
                    item1
                    for item1 in self._bridge_entity.bridge_config_data
                    if item1[VIVO_DEVICE_NAME_CONFIG_KEY] not in success_ids
                ]
            else:
                return
        VLog.info(
            _TAG,
            f"[async_handle_dev_unreg_result] after exclude:{self._bridge_entity.bridge_config_data}",
        )
        existing_entity_ids = {
            item[VIVO_DEVICE_ENTITY_ID_KEY]
            for item in self._bridge_entity.bridge_config_data
        }
        existing_mac_ids = {
            item[VIVO_HA_KEY_WORLD_DEV_LOGIC_MAC]
            for item in self._bridge_entity.bridge_config_data
        }
        await self._async_update_cache_for_unregister(
            existing_entity_ids, existing_mac_ids
        )
        await self._bridge_entity.bridge_config_handle.async_remove()
        await self._bridge_entity.bridge_config_handle.async_save(
            self._bridge_entity.bridge_config_data
        )
        await self._async_set_config_devices("unregister")
        await self.async_unregister_device_report()

    async def _async_device_enable_event(self, logic_mac: str, enable: bool):
        """Handle device enable event."""
        if self._bridge_entity is None:
            VLog.info(_TAG, f"[device_enable_event]：bridge has not initialized yet")
            return
        entity_id = Utils.get_entity_id_by_logic_mac(
            logic_mac, self._bridge_entity.bridge_config_data
        )
        if not entity_id:
            VLog.info(_TAG, f"[device_enable_event] entity_id:{logic_mac} not exist")
            return
        if enable:
            if self._cancel_ha_state_changed_listener_dict.get(entity_id) is None:
                VLog.info(
                    _TAG,
                    f"[device_enable_event] add {logic_mac},{entity_id} state change listener",
                )
                self._cancel_ha_state_changed_listener_dict[entity_id] = (
                    async_track_state_change_event(
                        self._bridge_entity.hass,
                        entity_id,
                        self._bridge_entity.async_handle_entity_state_change,
                        job_type=HassJobType.Coroutinefunction,
                    )
                )
            else:
                VLog.info(
                    _TAG,
                    f"[device_enable_event] {logic_mac},{entity_id} state change listener already exists",
                )
            device = {
                VIVO_HA_KEY_WORLD_DEV_LOGIC_MAC: logic_mac,
                VIVO_DEVICE_NAME_CONFIG_KEY: Utils.get_dn(
                    entity_id, self._bridge_entity.bridge_config_data
                ),
                VIVO_DEVICE_ENTITY_ID_KEY: entity_id,
                VIVO_DEVICE_NAME_FRIENDLY_KEY: Utils.get_fn(
                    entity_id, self._bridge_entity.bridge_config_data
                ),
                VIVO_HA_KEY_WORLD_DEV_ENTRY_ID: Utils.get_entry_id_from_entity_id(
                    entity_id, self._bridge_entity.bridge_config_data
                ),
            }
            self.get_bridge_entity().flush_device_status("device enable", device)
        else:
            cancel_listener = self._cancel_ha_state_changed_listener_dict.get(
                entity_id, None
            )
            if cancel_listener is not None:
                if callable(cancel_listener):
                    cancel_listener()
                    VLog.info(
                        _TAG,
                        f"[device_enable_event] delete listener {logic_mac}, {entity_id}",
                    )
                del self._cancel_ha_state_changed_listener_dict[entity_id]
            await self.get_bridge_entity().async_notify_device_offline(
                Utils.get_dn(entity_id, self._bridge_entity.bridge_config_data)
            )

    def _is_VHome_bridge_device(self, device: DeviceEntry) -> bool:
        connections_list = list(device.connections)
        if device.connections and len(connections_list[0]) == 2:
            VHome_bridge_mac = list(connections_list)[0][1]
            if VHome_bridge_mac == self._bridge_entity.config_entry.unique_id:
                return True
            else:
                return False
        else:
            return False

    async def _async_device_availability_update_event(
        self, event: Event[EventDeviceRegistryUpdatedData]
    ) -> None:
        if not event:
            VLog.warning(_TAG, "[device_availability_update_event] event is None")
            return
        if self._bridge_entity is None:
            VLog.info(
                _TAG,
                f"[device_availability_update_event]:bridge has not initialized yet",
            )
            return

        data = event.data
        VLog.info(_TAG, f"[device_availability_update_event] data ={data}")
        if (
            data.get("action") == "update"
            and "changes" in data
            and "disabled_by" in data["changes"]
        ):
            device_id = data.get("device_id", None)
            if not device_id:
                return
            VLog.info(_TAG, f"[device_availability_update_event] device {device_id}")
            _device = dr.async_get(self._bridge_entity.hass).async_get(device_id)
            if not _device:
                VLog.info(_TAG, f"[device_availability_update_event] device not exist")
                return
            device_availability = not _device.disabled_by
            if self._is_VHome_bridge_device(_device):
                VLog.info(
                    _TAG,
                    f"[device_availability_update_event] bridge changed {device_availability}",
                )
                if device_availability:
                    self._bridge_entity.set_device_enable(True)
                    bridge_device = DeviceManager.instance().get_bridge_device()
                    await DeviceManager.instance().async_connect(
                        bridge_device.host,
                        int(bridge_device.port),
                        bridge_device.name,
                        bridge_device.user_code,
                        "bridge_enable",
                    )
                else:
                    self._bridge_entity.set_device_enable(False)
                    if (
                        self.get_bridge_device_name() is not None
                        and len(self.get_bridge_device_name()) > 0
                    ):
                        VLog.info(
                            _TAG,
                            "[device_availability_update_event][async_disconnect] ...",
                        )
                        await self._vhome.async_disconnect(
                            self.get_bridge_device_name()
                        )
                return
            logic_mac = list(_device.identifiers)[0][2]
            VLog.info(
                _TAG,
                f"[device_availability_update_event] device {_device} \n "
                f"{self._bridge_entity.config_entry} \n "
                f"{self._bridge_entity.bridge_config_data}",
            )
            if not logic_mac:
                VLog.info(
                    _TAG, f"[device_availability_update_event] device no logic mac"
                )
                return
            if device_availability:
                await self._async_device_enable_event(logic_mac, True)
            else:
                await self._async_device_enable_event(logic_mac, False)

    async def _async_update_cache_for_unregister(
        self, existing_entity_ids: [], existing_mac_ids: []
    ) -> None:
        """
        remove the state change listener for the unregistered devices
        update _registered_device_mac_list
        """
        removed_entity_ids = [
            key
            for key in self._cancel_ha_state_changed_listener_dict.keys()
            if key not in existing_entity_ids
        ]
        VLog.info(
            _TAG,
            f"[update_cache_for_unregister] \n\t add {existing_entity_ids} "
            f"\n\t remove: {removed_entity_ids} "
            f"\n\t before mac list: {self._registered_device_mac_list}",
        )
        for listener_id, listener_value in list(
            self._cancel_ha_state_changed_listener_dict.items()
        ):
            if listener_id in removed_entity_ids:
                if listener_value is not None:
                    if callable(listener_value):
                        VLog.info(
                            _TAG,
                            f"[update_cache_for_unregister] cancel listen {listener_id}",
                        )
                        listener_value()
                    del self._cancel_ha_state_changed_listener_dict[listener_id]
        if not existing_mac_ids:
            self._registered_device_mac_list = []
        _filtered_mac_list = [
            mac for mac in self._registered_device_mac_list if mac in existing_mac_ids
        ]
        self._registered_device_mac_list = _filtered_mac_list
        VLog.info(
            _TAG,
            f"[update_cache_for_unregister] after mac list: {self._registered_device_mac_list}",
        )

    async def _async_handle_add_device_event(self, event) -> None:
        if self._bridge_entity is None:
            VLog.info(
                _TAG, f"[async_handle_add_device_event]：bridge has not initialized yet"
            )
            return
        config_data = self._bridge_entity.config_entry.data
        user_code = config_data.get(VIVO_BRIDGE_USER_CODE_CONFIG_KEY, None)
        device_name = config_data.get(VIVO_BRIDGE_DEVICE_NAME_CONFIG_KEY, None)
        mac = config_data.get(VIVO_BRIDGE_MAC_CONFIG_KEY, None)
        entity_id_list = event.data.get("data", [])
        VLog.info(
            _TAG, f"[async_handle_add_device_event] user add device:{entity_id_list}"
        )
        sub_devices: list = []
        logic_mac_entity_id_map = {}
        for entity_id in entity_id_list:
            node = VModel(
                self._bridge_entity.hass, self._bridge_entity.config_entry, entity_id
            )
            if node.model != {}:
                logic_mac = node.model.get(VIVO_HA_KEY_WORLD_DEV_LOGIC_MAC, None)
                if logic_mac is None:
                    continue
                logic_mac_entity_id_map[logic_mac] = entity_id
                sub_devices.append(node.model)

        reg_result = await self._async_register_sub_devices(
            user_code, device_name, mac, sub_devices
        )
        for success_item in reg_result["success"]:
            current_logic_mac = success_item[VIVO_HA_KEY_WORLD_DEV_LOGIC_MAC]
            # 检查 logicMac 是否在字典中
            if current_logic_mac in logic_mac_entity_id_map:
                # 若存在，添加 entity_id 到当前元素
                success_item[VIVO_DEVICE_ENTITY_ID_KEY] = logic_mac_entity_id_map[
                    current_logic_mac
                ]
        self._bridge_entity.hass.bus.async_fire(EVENT_VHOME_DEV_REG_RESULT, reg_result)

    async def _async_register_sub_devices(
        self, user_code: str, device_name: str, mac: str, sub_devices: list[dict]
    ) -> dict:
        result = await self._vhome.async_sub_devices_register(
            user_code, device_name, mac, sub_devices
        )
        VLog.info(
            _TAG,
            f"[_async_register_sub_devices] sub devices \n\t size {len(sub_devices)} "
            f"\n\t{sub_devices} \n\tresult:{result}",
        )
        if result.get("success", None) is not None:
            self._registered_device_mac_list = [
                item.get(VIVO_HA_KEY_WORLD_DEV_LOGIC_MAC)
                for item in result.get("success")
            ]
        return result

    async def _async_handle_state_change_event(self, event) -> None:
        VLog.info(_TAG, "_async_handle_state_change_event")
        bridge_device = DeviceManager.instance().get_bridge_device()
        if (
            bridge_device.host is None
            or bridge_device.port is None
            or bridge_device.name is None
            or bridge_device.user_code is None
        ):
            VLog.warning(
                _TAG,
                f"Bridge_device data:{bridge_device} is not useful,don't async_data_report",
            )
            return
        await self.async_data_report(
            event.data.get(VIVO_DEVICE_NAME_CONFIG_KEY), event.data.get("data")
        )

    async def _async_handle_state_flush_event(self, event) -> None:
        if self._bridge_entity is None:
            VLog.info(
                _TAG, f"[handle_state_flush_event]：bridge has not initialized yet"
            )
            return
        devices = event.data.get("devices")
        VLog.info(_TAG, f"[handle_state_flush_event] flush device:{devices}")
        if devices is not None:
            for device in devices:
                self._bridge_entity.flush_device_status("event", device)

    async def _async_handle_bridge_online_event(self, event) -> None:
        """
        Bridge online,
        local device synchronization to the server
        reporting the status of local device
        """
        if self._bridge_entity is None:
            VLog.info(
                _TAG,
                f"[_async_handle_bridge_online_event]：bridge has not initialized yet",
            )
            return
        VLog.info(_TAG, f"[_async_handle_bridge_online_event]")
        await self._reconnector.stop_reconnect("online_state")
        await self.async_data_report(
            None,
            {
                VIVO_HA_COMMON_ATTR_MODEL: GLOB_NAME,
                VIVO_ATTR_NAME_ONLINE: "true",
                VIVO_HA_COMMOM_ATTR_SOFTVER: self.integration_version,
                VIVO_HA_COMMOM_ATTR_HARDVER: __version__,
                VIVO_HA_COMMOM_ATTR_VENDOR: Utils.get_cpuinfo_model(),
                VIVO_HA_COMMON_ATTR_SERIAL: self.get_bridge_mac()
                if self.get_bridge_mac() is not None
                else "",
            },
        )
        await self.async_unregister_device_report()
        config_entry = self._bridge_entity.config_entry
        await self.async_sync_sub_devices(config_entry, "connect_established")
        devices = self.get_device_list(config_entry)
        for device in devices:
            dn = device.get(VIVO_DEVICE_NAME_CONFIG_KEY, None)
            device_id = device.get(VIVO_DEVICE_ID_KEY, None)
            if not dn:
                VLog.info(
                    _TAG,
                    f"[_async_handle_bridge_online_event] flush {device} but dn is not exist",
                )
                continue
            if not device_id:
                VLog.info(
                    _TAG,
                    f"[_async_handle_bridge_online_event] flush {device} but device_id is not exist",
                )
                continue
            if await self._async_device_is_enable(device_id):
                self.get_bridge_entity().flush_device_status(
                    "connect established", device
                )
            else:
                VLog.info(
                    _TAG,
                    f"[_async_handle_bridge_online_event] flush {device} but is disable",
                )
                await self.get_bridge_entity().async_notify_device_offline(dn)

    async def _async_handle_reconnect_event(self, event) -> None:
        VLog.info(_TAG, f"[_async_handle_reconnect_event] event {event}")
        host = event.data.get(VIVO_BRIDGE_HOST_CONFIG_KEY)
        port = event.data.get(VIVO_BRIDGE_PORT_CONFIG_KEY)
        device_name = event.data.get(VIVO_BRIDGE_DEVICE_NAME_CONFIG_KEY)
        user_code = event.data.get(VIVO_BRIDGE_USER_CODE_CONFIG_KEY)
        reason = event.data.get("reason")
        self._reconnector.start_reconnect(
            host, int(port), device_name, user_code, reason
        )

    async def _async_set_config_devices(self, reason: str):
        if self._bridge_entity is None:
            VLog.info(_TAG, f"[set_config_devices] bridge has not initialized yet")
            return
        entry_data = self._bridge_entity.config_entry.data.copy()
        entry_data[VIVO_HA_CONFIG_DATA_DEVICES_KEY] = (
            self._bridge_entity.bridge_config_data
        )
        VLog.info(_TAG, f"[set_config_devices][{reason}] " + json.dumps(entry_data))
        devices = entry_data[VIVO_HA_CONFIG_DATA_DEVICES_KEY]
        if devices is not None:
            dev_reg = dr.async_get(self._bridge_entity.hass)
            reg_devices = list(dev_reg._device_data.values())
            for reg_device_item in reg_devices:
                config_entries = list(reg_device_item.config_entries)
                if (
                    self._bridge_entity.config_entry.entry_id in config_entries
                    and reg_device_item.entry_type is not dr.DeviceEntryType.SERVICE
                ):
                    reg_flag = False
                    for device in devices:
                        local_logic_mac = device.get(VIVO_HA_KEY_WORLD_DEV_LOGIC_MAC)
                        if local_logic_mac == list(reg_device_item.identifiers)[0][2]:
                            reg_flag = True
                            if reg_device_item.disabled_by:
                                VLog.info(
                                    _TAG,
                                    f"[set_config_devices][{reason}] has been disabled "
                                    f"uuid：{local_logic_mac} id：{reg_device_item.id}",
                                )
                                await self._async_device_enable_event(
                                    local_logic_mac, False
                                )
                            VLog.info(
                                _TAG,
                                f"[set_config_devices][{reason}] register device "
                                f"uuid：{local_logic_mac} id：{reg_device_item.id}",
                            )
                            break
                    if not reg_flag:
                        dev_reg.async_remove_device(reg_device_item.id)
                        cancel_listener = (
                            self._cancel_listen_device_registry_updated_dict.get(
                                reg_device_item.id, None
                            )
                        )
                        if cancel_listener is not None:
                            if callable(cancel_listener):
                                VLog.info(
                                    _TAG,
                                    f"[set_config_devices][{reason}] delete listener"
                                    f"{reg_device_item.identifiers} {reg_device_item.id}",
                                )
                                cancel_listener()
                            del self._cancel_listen_device_registry_updated_dict[
                                reg_device_item.id
                            ]
                        VLog.info(
                            _TAG,
                            f"[set_config_devices][{reason}] delete device"
                            f"{reg_device_item.identifiers} {reg_device_item.id}",
                        )
            for device in devices:
                connection = (
                    dr.CONNECTION_NETWORK_MAC,
                    device[VIVO_HA_KEY_WORLD_DEV_LOGIC_MAC],
                )
                identifier = (
                    DOMAIN,
                    self._bridge_entity.config_entry.entry_id,
                    device[VIVO_HA_KEY_WORLD_DEV_LOGIC_MAC],
                )
                manufacturer = ""
                model = ""
                area = ""
                entity_id = device[VIVO_DEVICE_ENTITY_ID_KEY]
                entity_obj = er.async_get(self._bridge_entity.hass).async_get(entity_id)
                device_name = device.get(ATTR_FRIENDLY_NAME, "")
                if entity_obj is None or entity_obj.device_id is None:
                    VLog.warning(
                        _TAG,
                        f"[set_config_devices][{reason}] {entity_id}:"
                        f"entity_obj or entity_obj.device_id is None",
                    )
                else:
                    _device = dr.async_get(self._bridge_entity.hass).async_get(
                        entity_obj.device_id
                    )
                    if _device is not None:
                        manufacturer = _device.manufacturer or ""
                        model = _device.model or ""
                        device_name = self._generate_device_name_of_bridge(
                            entity_id, device_name, _device
                        )
                if device_name is None:
                    device_name = entity_id
                new_device = dev_reg.async_get_or_create(
                    config_entry_id=self._bridge_entity.config_entry.entry_id,
                    identifiers={identifier},
                    connections={connection},
                    manufacturer=manufacturer,
                    name=device_name,
                    model=model,
                    # suggested_area=area,
                )
                VLog.info(
                    _TAG,
                    f"[set_config_devices][{reason}] new device:{new_device} "
                    f"uuid:{list(new_device.identifiers)[0][2]} id:{new_device.id}",
                )
                if (
                    self._cancel_listen_device_registry_updated_dict.get(new_device.id)
                    is None
                ):
                    VLog.info(
                        _TAG,
                        f"[set_config_devices][{reason}] "
                        f"add {device_name} {new_device.id} device listener",
                    )
                    self._cancel_listen_device_registry_updated_dict[new_device.id] = (
                        async_track_device_registry_updated_event(
                            self._bridge_entity.hass,
                            new_device.id,
                            self._async_device_availability_update_event,
                            job_type=HassJobType.Coroutinefunction,
                        )
                    )
                else:
                    VLog.info(
                        _TAG,
                        f"[set_config_devices][{reason}] {device_name} device listener already exists",
                    )

        if entry_data:
            self._bridge_entity.hass.config_entries.async_update_entry(
                self._bridge_entity.config_entry, data=entry_data
            )
        else:
            self._bridge_entity.hass.config_entries.async_update_entry(
                self._bridge_entity.config_entry
            )

    def _generate_device_name_of_bridge(
        self, entity_id: str, friendly_name: str, device: DeviceEntry
    ) -> str:
        platform_name = entity_id.split(".")[0]
        _result = friendly_name
        if _result is None or len(_result) == 0:
            # friendly_name is empty,then set as device name
            _result = device.name_by_user or device.name
        if _result is None or len(_result) == 0:
            # friendly_name or device name is empty ,then set entity id
            return entity_id
        # _area_name = device.suggested_area
        # if _area_name:
        #     _result += f" - {_area_name} "
        if platform_name:
            _result += f" ({platform_name})"
        return _result

    """ private method end"""

    async def _async_device_is_enable(self, device_id: str):
        if self._bridge_entity is None:
            VLog.info(_TAG, f"[async_device_is_enable] bridge has not initialized yet")
            return False
        _device = dr.async_get(self._bridge_entity.hass).async_get(device_id)
        if not _device:
            VLog.info(_TAG, f"[async_device_is_enable] {device_id} not exist")
            return False
        if _device.disabled_by:
            VLog.debug(_TAG, f"[async_device_is_enable] {device_id} is disable")
            return False
        return True
