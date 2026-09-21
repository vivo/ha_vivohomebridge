"""
Copyright 2024 vivo Mobile Communication Co., Ltd.
Licensed under the Apache License, Version 2.0 (the "License");

   http://www.apache.org/licenses/LICENSE-2.0
"""

import asyncio
import uuid
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EVENT_HOMEASSISTANT_STARTED
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType
from .const import (
    EVENT_VHOME_DEV_REMOVE_BRIDGE,
    VIVO_BRIDGE_BOOT_UP_REASON_KEY,
    VIVO_HA_BRIDGE_VERSION,
    DOMAIN,
)
from .v_local_service import VLocalService
from .device_manager import DeviceManager
from .v_utils.vlog import VLog
from .vbridge import VBridgeEntity

_TAG = "entry_config"


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up an entry."""
    boot_up_reason = entry.data.get(VIVO_BRIDGE_BOOT_UP_REASON_KEY, "home_assistant")
    VLog.info(_TAG, f"[setup entry] setup from:{boot_up_reason},data:{entry.data}")
    if boot_up_reason == "home_assistant":

        async def _async_initialize(event):
            VLog.info(_TAG, f"[setup entry] async_initialize")
            await _async_init(hass, entry)

        hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STARTED, _async_initialize)
    else:
        if boot_up_reason == "unload":
            try:
                await asyncio.sleep(2)
            except asyncio.CancelledError as e:
                VLog.info(_TAG, f"[async_setup_entry] sleep exception:{e}")
        VLog.info(_TAG, f"[setup entry]={boot_up_reason}")
        _entry_data = entry.data.copy()
        _entry_data[VIVO_BRIDGE_BOOT_UP_REASON_KEY] = "home_assistant"
        hass.config_entries.async_update_entry(entry, data=_entry_data)
        await _async_init(hass, entry)

    return True


async def _async_init(hass, entry):
    bridge_entity = VBridgeEntity(hass, entry)
    DeviceManager.instance().set_bridge(bridge_entity)
    DeviceManager.instance().set_local_service(hass)
    await DeviceManager.instance().async_dm_service_start(hass)


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    VLog.info(_TAG, f"[async_remove_entry]{entry.data}")
    await DeviceManager.instance().async_remove_sub_devices()
    await DeviceManager.instance().async_bridge_remove()
    return True


async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Unload a config entry. when forbidden the entry."""
    _entry_data = config_entry.data.copy()
    _entry_data[VIVO_BRIDGE_BOOT_UP_REASON_KEY] = "unload"
    hass.config_entries.async_update_entry(config_entry, data=_entry_data)

    VLog.info(_TAG, f"[async_unload_entry]{config_entry.data}")
    DeviceManager.instance().instance().get_local_server().config_flag(2)
    await DeviceManager.instance().instance().get_local_server().sync_update_txt()
    await DeviceManager.instance().instance().get_local_server().sync_stop()
    await DeviceManager.instance().instance().get_vhome().network_shakehand_task_stop()
    await DeviceManager.instance().uninstall()
    return True
