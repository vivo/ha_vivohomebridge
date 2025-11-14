"""
Copyright 2024 vivo Mobile Communication Co., Ltd.
Licensed under the Apache License, Version 2.0 (the "License");

   http://www.apache.org/licenses/LICENSE-2.0
"""

import asyncio
import base64
import io
import json
import time
import uuid
from typing import Any
import qrcode
import voluptuous as vol
from functools import partial
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.const import ATTR_ENTITY_ID, ATTR_NAME
from homeassistant.core import callback
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.instance_id import async_get
from . import DeviceManager
from .const import (
    DOMAIN,
    GLOB_NAME,
    VIVO_HA_CONFIG_DATA_DEVICES_KEY,
    VIVO_HA_CONF_DEVICE_LIST,
    EVENT_VHOME_DEV_UNREG_RESULT,
    VIVO_HA_KEY_WORLD_DEV_LOGIC_MAC,
    VIVO_BRIDGE_DEVICE_NAME_CONFIG_KEY,
    VIVO_BRIDGE_HOST_CONFIG_KEY,
    VIVO_BRIDGE_MAC_CONFIG_KEY,
    VIVO_BRIDGE_PORT_CONFIG_KEY,
    VIVO_DEVICE_NAME_CONFIG_KEY,
    VIVO_BRIDGE_USER_CODE_CONFIG_KEY,
    VIVO_BRIDGE_BOOT_UP_REASON_KEY,
    NOTE_URL,
    VIVO_HA_CONF_BIND_CODE,
    VIVO_TIMEOUT_EXPIRED_TS,
)
from .v_utils.vlog import VLog

_TAG = "device_config"
_EXPIRE_IN = "expireIn"
_BIND_CODE = "bindCode"


class VHomeBridgeConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1
    __DEFAULT_TIME_OUT = 300

    def __init__(self):
        self._enable = False
        self._bridge_mac = ""
        self._bind_code = ""
        self._qrcode_base64 = ""
        self.qrcode_abort_msg_id = ""
        self._bridge_data = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        self.hass.data.setdefault(DOMAIN, {})
        errors: dict[str, str] = {}
        description_placeholders: {} = {}
        if user_input is not None:
            if user_input.get("important_notes", None) is True:
                self._bridge_mac = f"{await async_get(self.hass)}{int(time.time())}"
                VLog.info(
                    _TAG, "[async_step_user]bridge mac: {}".format(self._bridge_mac)
                )
                cp_data = {
                    VIVO_BRIDGE_MAC_CONFIG_KEY: self._bridge_mac,
                    VIVO_BRIDGE_BOOT_UP_REASON_KEY: "config_flow",
                }
                self._bridge_data = cp_data
                await self.async_set_unique_id(self._bridge_mac)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=f"{GLOB_NAME}",
                    data=self._bridge_data,
                )
            errors["base"] = "important_notes_not_agree"
        description_placeholders["note_url"] = NOTE_URL

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {vol.Required("important_notes", default=False): bool}
            ),
            last_step=False,
            errors=errors,
            description_placeholders=description_placeholders,
        )

    @callback
    def async_remove(self) -> None:
        self._enable = False
        VLog.info(_TAG, f"[async_remove] ...")
        super().async_remove()

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Get the options flow for this handler."""
        return VHomeBridgeOptionsFlowHandler(config_entry)

    def __generate_bridge_mac(self) -> str:
        mac_from_uuid = uuid.UUID(int=uuid.getnode()).hex[-12:]
        bridge_mac = ":".join(
            mac_from_uuid[i : i + 2] for i in range(0, len(mac_from_uuid), 2)
        )
        return bridge_mac


class VHomeBridgeOptionsFlowHandler(OptionsFlow):
    __DEFAULT_TIME_OUT = 300

    def __init__(self, config_entry: ConfigEntry):
        self._enable = True
        self.config_entry = config_entry
        self._bind_code = ""
        self._qrcode_base64 = self.__generate_qrcode_base64("https://example.com")
        self._delay_time = self.__DEFAULT_TIME_OUT
        self.qrcode_abort_msg_id = ""
        self._qrcode_scanned_task: asyncio.Task | None = None
        self._bridge_data = {}
        VLog.debug(_TAG, "[__init__] VHomeBridgeOptionsFlowHandler...")
        VLog.debug(_TAG, f"[__init__] config_entry: {config_entry}")

    def __generate_qr_code(self, bind_code: str):
        data = {"ha_bind_code": bind_code}
        json_data = json.dumps(data)
        return json_data

    def __generate_qrcode_base64(self, qrcode_str: str):
        try:
            qr_code = qrcode_str
            qr = qrcode.QRCode(
                version=5,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(qr_code)
            qr.make(fit=True)
            img = qr.make_image(fill="black", back_color="white")

            # 将二维码转换为Base64编码的字符串
            buffered = io.BytesIO()
            img.save(buffered, format="PNG")
            return base64.b64encode(buffered.getvalue()).decode("utf-8")
        except Exception as e:
            VLog.error(_TAG, f"[generate_qrcode_base64] failed: {e}")
            return None

    async def async_step_qrcode_show(self, user_input: dict[str, Any] | None = None):
        img_base64 = self._qrcode_base64
        self._enable = True

        VLog.debug(_TAG, f"[async_step_qrcode_show] img_base64: {img_base64}")

        async def _wait_for_scanned() -> None:
            # 3 seconds is network latency, redundant design
            current_timestamp = time.time()
            timeout = self._delay_time - 3
            if timeout <= 0:
                timeout = self.__DEFAULT_TIME_OUT - 3
            bind_code = self._bind_code
            mac = self.config_entry.data.get(VIVO_BRIDGE_MAC_CONFIG_KEY)
            while True:
                if self._enable is False:
                    break
                try:
                    await asyncio.sleep(2)
                except asyncio.CancelledError:
                    VLog.info(_TAG, f"[wait_for_scanned] check scan task canceled")
                    raise
                _current_timestamp = time.time()
                if _current_timestamp - current_timestamp > timeout:
                    self.qrcode_abort_msg_id = "timeout_abort"
                    raise TimeoutError("QR code scan timed out")
                VLog.info(_TAG, f"[wait_for_scanned] check scan {bind_code}")
                bind_result_dict = (
                    await DeviceManager.instance()
                    .get_vhome()
                    .async_bind(bind_code, mac, GLOB_NAME)
                )
                if bind_result_dict is None or len(bind_result_dict) == 0:
                    VLog.info(
                        _TAG, f"[wait_for_scanned] error bind_result_dict no data"
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
                    self._bridge_data = cp_data
                    VLog.info(_TAG, f"[wait_for_scanned] scanned {bind_code}")
                    break
                else:
                    VLog.info(_TAG, f"[wait_for_scanned] error {bind_result_code}")
                    continue

        if self._qrcode_scanned_task is None:
            self._qrcode_scanned_task = self.hass.async_create_task(
                partial(
                    DeviceManager.instance().async_binding_pending,
                    1,
                    self._bind_code,
                    self.config_entry.data.get(VIVO_BRIDGE_MAC_CONFIG_KEY),
                    self._delay_time,
                )()
            )

        if self._qrcode_scanned_task.done():
            if err := self._qrcode_scanned_task.exception():
                if isinstance(err, TimeoutError):
                    VLog.info(
                        _TAG, f"Occur error while waiting for scanned task: {err}"
                    )
                    self.qrcode_abort_msg_id = "timeout_abort"
                else:
                    VLog.info(_TAG, f"Unexpected error waiting for scanned task: {err}")
                    self.qrcode_abort_msg_id = "network_abort"
            else:
                VLog.debug(_TAG, "[async_step_qrcode_show] scanned task done")
                self.qrcode_abort_msg_id = ""
            return self.async_show_progress_done(next_step_id="qrcode_scanned")

        await DeviceManager.instance().get_vhome().network_shakehand_task_stop()
        await DeviceManager.instance().instance().get_local_server().sync_stop()
        if self._delay_time % 60 == 0:
            time_out_minutes = self._delay_time / 60
            unit_key = "min"
        else:
            time_out_minutes = self._delay_time
            unit_key = "sec"
        TIME_UNIT_TRANSLATIONS = {
            "zh-Hans": {"min": "分钟", "sec": "秒"},
            "en": {"min": "minute", "sec": "second"},
        }
        lang = self.hass.config.language
        time_unit = TIME_UNIT_TRANSLATIONS.get(lang, TIME_UNIT_TRANSLATIONS["en"])[unit_key]
        return self.async_show_progress(
            step_id="qrcode_show",
            progress_action="wait_for_scanned",
            description_placeholders={
                "img_base64": img_base64,
                "time_out": time_out_minutes,
                "time_unit": time_unit,
            },
            progress_task=self._qrcode_scanned_task,
        )

    async def async_step_qrcode_scanned(self, user_input=None) -> ConfigFlowResult:
        if self.qrcode_abort_msg_id != "":
            VLog.info(
                _TAG,
                f"[async_step_qrcode_scanned] qrcode_abort_msg_id={self.qrcode_abort_msg_id}",
            )
            return self.async_abort(reason=self.qrcode_abort_msg_id)
        return await self.async_step_select_device()

    async def async_step_qrcode_process(self) -> ConfigFlowResult:
        VLog.info(_TAG, f"[async_step_qrcode_process] ...")
        errors: dict[str, str] = {}
        description_placeholders: str = {}
        bind_code: str = None
        _delay_time: int = 300

        mac = self.config_entry.data.get(VIVO_BRIDGE_MAC_CONFIG_KEY)
        bcode_dict_result = (
            await DeviceManager.instance().get_vhome().async_get_bcode(mac)
        )
        VLog.info(_TAG, f"[_handle_bcode_async] bcode_dict_result:{bcode_dict_result}")

        if bcode_dict_result is None or bcode_dict_result.get("data") is None:
            errors["base"] = "network_error"
            description_placeholders = {"code": "1000"}
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
                description_placeholders = {"code": "1001"}
            else:
                VLog.debug(_TAG, f"[async_get_bcode] bind_code:{bind_code}")
                self._bind_code = bind_code
                qrcode_str = self.__generate_qr_code(bind_code)
                VLog.debug(_TAG, f"qrcode_str:{qrcode_str}")
                self._qrcode_base64 = self.__generate_qrcode_base64(qrcode_str)
                if self._qrcode_base64 is None or self._qrcode_base64 == "":
                    errors["base"] = "network_error"
                    description_placeholders = {"code": "1002"}
                else:
                    return await self.async_step_qrcode_show()
        else:
            VLog.warning(_TAG, f"[async_get_bcode] failed {bcode_dict_result}")
            code = bcode_dict_result.get("code")
            errors["base"] = "network_error"
            description_placeholders = {"code": str(code)}

        return self.async_show_form(
            step_id="qrcode_process",
            last_step=False,
            errors=errors,
            description_placeholders=description_placeholders,
        )

    async def async_step_select_device(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        config_devices = self.config_entry.data.get(VIVO_HA_CONFIG_DATA_DEVICES_KEY)
        bridge_device_name = ""
        if VIVO_BRIDGE_DEVICE_NAME_CONFIG_KEY in self.config_entry.data:
            bridge_device_name = self.config_entry.data.get(
                VIVO_BRIDGE_DEVICE_NAME_CONFIG_KEY
            )
        if user_input is not None:
            if (
                DeviceManager.instance().get_bridge_entity().get_device_enable()
                is False
            ):
                return self.async_abort(reason="bridge_device_disable")
            select_device_entity_ids = user_input.get(VIVO_HA_CONF_DEVICE_LIST, [])
            if config_devices is not None and len(config_devices) > 0:
                for config_device_item in config_devices:
                    device_entity_id = config_device_item.get(ATTR_ENTITY_ID)
                    if device_entity_id not in select_device_entity_ids:
                        VLog.info(
                            _TAG, f"[async_step_init] user unselect:{device_entity_id}"
                        )
                        un_reg_logic_mac = config_device_item.get(
                            VIVO_HA_KEY_WORLD_DEV_LOGIC_MAC
                        )
                        DeviceManager.instance().get_bridge_entity().hass.bus.fire(
                            EVENT_VHOME_DEV_UNREG_RESULT,
                            {
                                "success": [
                                    {VIVO_HA_KEY_WORLD_DEV_LOGIC_MAC: un_reg_logic_mac}
                                ],
                                "failed": [],
                            },
                        )
            await DeviceManager.instance().on_async_ui_select_device(
                select_device_entity_ids
            )
            host = ""
            port = ""
            mac = ""
            if VIVO_BRIDGE_HOST_CONFIG_KEY in self.config_entry.data:
                host = self.config_entry.data.get(VIVO_BRIDGE_HOST_CONFIG_KEY)
            if VIVO_BRIDGE_PORT_CONFIG_KEY in self.config_entry.data:
                port = self.config_entry.data.get(VIVO_BRIDGE_PORT_CONFIG_KEY)
            if VIVO_BRIDGE_MAC_CONFIG_KEY in self.config_entry.data:
                mac = self.config_entry.data.get(VIVO_BRIDGE_MAC_CONFIG_KEY)
            return self.async_create_entry(
                title=f"网关设备id：{bridge_device_name}",
                data={
                    VIVO_BRIDGE_DEVICE_NAME_CONFIG_KEY: bridge_device_name,
                    VIVO_BRIDGE_HOST_CONFIG_KEY: host,
                    VIVO_BRIDGE_PORT_CONFIG_KEY: port,
                    VIVO_BRIDGE_MAC_CONFIG_KEY: mac,
                },
            )
        bridge_entity = DeviceManager.instance().get_bridge_entity()
        if bridge_entity is None:
            return self.async_abort(reason="integration_not_init")
        options_source_list = (
            await DeviceManager.instance().get_bridge_entity().get_supported_list()
        )
        """
        [{'entity_id': 'xxxxa','name': 'yyyya'},{'entity_id': 'xxxxb','name': 'yyyyb'}]
        convert to
        [{'xxxxa': 'yyyya'},{'xxxxb': 'yyyyb'}]
        """
        options_dict = {
            item[ATTR_ENTITY_ID]: item[ATTR_NAME] for item in options_source_list
        }
        default_selected_entity_id_list = []
        if (
            config_devices is not None
            and len(bridge_device_name) > 0
            and len(config_devices) > 0
        ):
            default_selected_entity_id_list = [
                config_device_item[ATTR_ENTITY_ID]
                for config_device_item in config_devices
                if config_device_item[ATTR_ENTITY_ID] in options_dict
            ]
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        VIVO_HA_CONF_DEVICE_LIST,
                        default=default_selected_entity_id_list,
                    ): cv.multi_select(options_dict),
                }
            ),
        )

    async def _is_bound(self):
        return self.config_entry.data.get(VIVO_BRIDGE_DEVICE_NAME_CONFIG_KEY, None)

    async def async_step_finish(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        return self.async_abort(reason="wait_config")

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        VLog.debug(_TAG, f"[async_step_init] user_input:{user_input}")
        VLog.debug(_TAG, f"_is_bound={await self._is_bound()}")
        VLog.debug(_TAG, f"_qrcode_base64={self._qrcode_base64}")
        if (
            DeviceManager.instance().get_config_state()
            == DeviceManager.VConfig_STATE.STATE_LAN
        ):
            return await self.async_step_finish()
        if await self._is_bound() is None:
            return await self.async_step_qrcode_process()
        return await self.async_step_select_device(user_input)
