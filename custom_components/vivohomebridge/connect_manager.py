"""
 Copyright 2024 vivo Mobile Communication Co., Ltd.
 Licensed under the Apache License, Version 2.0 (the "License");

    http://www.apache.org/licenses/LICENSE-2.0
"""
import asyncio
from homeassistant.core import HomeAssistant
from custom_components.vivohomebridge.const import EVENT_VHOME_HOST_LIST_GET

from .v_utils.vlog import VLog

_TAG = "ReconnectManager"


def singleton(cls):
    instances = {}

    def get_instance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]

    return get_instance


@singleton
class ReconnectManager:

    def __init__(self,vhome):
        self._vhome = vhome
        self._stop_event = asyncio.Event()
        self._reconnect_task = None
        self.hass: HomeAssistant = None
        self.host_list: list[str] = []

    async def async_connect(self, host: str, port: int, dn: str, user_code: str, reason: str) -> None:
        if self._vhome is None:
            VLog.error(_TAG, f"[async_connect]:vhome has not initialized yet when {reason}")
            return
        connect_result = await self._vhome.async_connect(host, port, dn, user_code)
        if connect_result != 0:
            VLog.info(_TAG, f"[async_connect]:connect failure {connect_result} when {reason}")
            self.start_reconnect(host, port, dn, user_code, reason)
        else:
            VLog.info(_TAG, f"[async_connect]:connect success {connect_result} when {reason}")

    def start_reconnect(self, host: str, port: int, dn: str, user_code: str, reason: str) -> None:
        # task 意外死亡(done 但 stop_event 未 set)时也允许重建；
        # stop_event 已 set 时循环本身会立即退出，不会误重启
        if self._reconnect_task is None or self._reconnect_task.done():
            try:
                self._reconnect_task = asyncio.create_task(self._reconnect_loop(host, port, dn, user_code, reason))
            except Exception as e:
                VLog.error(_TAG, f"Failed to create reconnect task: {e}")
        else:
            VLog.warning(_TAG, f"[start_reconnect]:reconnect task already running when {reason}")

    async def _reconnect_loop(self, host, port, dn, user_code, reason) -> None:
        _host = host
        _port = port
        _host_list = self.host_list
        _retry_count = 0          # 当前 host 已重试次数
        _host_tried_count = 0     # 已尝试过的 host 数（切换时累加）
        while not self._stop_event.is_set():
            try:
                VLog.info(_TAG, f"[reconnect_loop][{reason}] reconnect after 5 second")
                await asyncio.sleep(5)
            except asyncio.CancelledError as err:
                VLog.info(_TAG, f"[reconnect_loop] cancel when {reason}:{err}")
                break
            try:
                VLog.info(_TAG, f"[reconnect_loop][{reason}] {_host}:{_port} reconnecting... (retry {_retry_count}/3)")
                connect_result = await self._vhome.async_connect(_host, _port, dn, user_code)
                if connect_result == 0:
                    VLog.info(_TAG, f"[reconnect_loop][{reason}] reconnected")
                    await self.stop_reconnect("reconnected")
                    break
                else:
                    # 同一个 host 重试 3 次都失败，切换到 host_list 下一个
                    _retry_count += 1
                    if _retry_count < 3:
                        VLog.info(_TAG, f"[reconnect_loop][{reason}] {_host}:{_port} failed, retry count {_retry_count}/3")
                        continue
                    # 已重试 3 次，切换到下一个 host
                    _retry_count = 0
                    if _host_list and len(_host_list) > 0:
                        current = f"{_host}:{_port}"
                        idx = _host_list.index(current) if current in _host_list else -1
                        next_host_port = _host_list[(idx + 1) % len(_host_list)]
                        _host, port_str = next_host_port.rsplit(":", 1)
                        _port = int(port_str)
                        _host_tried_count += 1
                        VLog.info(_TAG, f"[reconnect_loop][{reason}] switch to next host {_host}:{_port} (host tried {_host_tried_count}/{len(_host_list)})")
                        # host_list 全部尝试完都失败，触发重新拉取 host_list，不 break 继续循环
                        if _host_tried_count >= len(_host_list):
                            _host_tried_count = 0
                            VLog.info(_TAG, f"[reconnect_loop][{reason}] all {len(_host_list)} hosts tried, fire {EVENT_VHOME_HOST_LIST_GET}")
                            if self.hass is not None:
                                self.hass.bus.fire(EVENT_VHOME_HOST_LIST_GET, {})
            except Exception as e:
                VLog.info(_TAG, f"[reconnect_loop][{reason}] reconnect failed: {e}")

    async def stop_reconnect(self, reason: str):
        self._stop_event.set()
        if self._reconnect_task is not None and not self._reconnect_task.done():
            VLog.info(_TAG, f"[stop_reconnect][{reason}] reconnect_task cancel")
            self._reconnect_task.cancel()
        self._stop_event.clear()
        self._reconnect_task = None

    def is_reconnect_task_active(self) -> bool:
        if self._reconnect_task is not None:
            return not self._reconnect_task.done()
        return False