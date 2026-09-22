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


def parse_host_port(entry: str) -> tuple[str | None, int | None]:
    """解析 "ip:port" 字符串，格式非法时返回 (None, None)。

    用 rsplit(":", 1) 保留 IPv6 字面量的方括号(如 "[::1]:8080")；
    端口非数字同样视为非法。调用方不应再用 f"{host}:{port}" 回拼去
    匹配原始列表项——端口前导零("08080" -> 8080)会导致匹配失败。
    """
    if not entry or not isinstance(entry, str):
        return None, None
    parts = entry.rsplit(":", 1)
    if len(parts) != 2:
        return None, None
    try:
        return parts[0], int(parts[1])
    except ValueError:
        return None, None


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
        # 用显式索引轮询，不再用 f"{host}:{port}" 回拼去匹配列表项：
        # 端口带前导零("08080"->8080)会让字符串匹配失败，idx 退化为 -1，
        # 导致每轮都回到 host_list[0]，多接入点轮询彻底失效。
        # 每轮从 self.host_list 现取，云端更新列表后无需重启循环即可感知。
        _retry_count = 0          # 当前 host 已重试次数
        _host_tried_count = 0     # 已尝试过的 host 数（切换时累加）
        _idx = self._locate_start_index(host, port)

        while not self._stop_event.is_set():
            try:
                VLog.info(_TAG, f"[reconnect_loop][{reason}] reconnect after 5 second")
                await asyncio.sleep(5)
            except asyncio.CancelledError as err:
                VLog.info(_TAG, f"[reconnect_loop] cancel when {reason}:{err}")
                break
            try:
                # 每轮现取列表，长度可能因云端更新而变化
                host_list = self.host_list
                if not host_list:
                    VLog.warning(_TAG, f"[reconnect_loop][{reason}] host_list empty, wait and retry")
                    await asyncio.sleep(10)
                    continue

                _idx %= len(host_list)
                _host, _port = parse_host_port(host_list[_idx])
                if _host is None:
                    # 单条格式非法：跳过该项，不让整个循环退出
                    VLog.error(_TAG, f"[reconnect_loop][{reason}] invalid entry {host_list[_idx]!r}, skip")
                    _idx += 1
                    _host_tried_count += 1
                    if _host_tried_count >= len(host_list):
                        _host_tried_count = 0
                        self._fire_host_list_get(reason)
                    continue

                VLog.info(_TAG, f"[reconnect_loop][{reason}] {_host}:{_port} reconnecting... (retry {_retry_count}/3, idx {_idx}/{len(host_list)})")
                connect_result = await self._vhome.async_connect(_host, _port, dn, user_code)
                if connect_result == 0:
                    VLog.info(_TAG, f"[reconnect_loop][{reason}] reconnected")
                    await self.stop_reconnect("reconnected")
                    break

                # 同一个 host 重试 3 次都失败，切换到 host_list 下一个
                _retry_count += 1
                if _retry_count < 3:
                    VLog.info(_TAG, f"[reconnect_loop][{reason}] {_host}:{_port} failed, retry count {_retry_count}/3")
                    continue

                _retry_count = 0
                _idx += 1
                _host_tried_count += 1
                VLog.info(_TAG, f"[reconnect_loop][{reason}] switch to next idx {_idx % len(host_list)} (host tried {_host_tried_count}/{len(host_list)})")
                # host_list 全部尝试完都失败，触发重新拉取，不 break 继续轮询
                if _host_tried_count >= len(host_list):
                    _host_tried_count = 0
                    self._fire_host_list_get(reason)
            except Exception as e:
                # 注意: 不捕获 asyncio.CancelledError(它继承 BaseException)，
                # 取消信号必须向上传播，否则 task 无法被正确取消
                VLog.info(_TAG, f"[reconnect_loop][{reason}] reconnect failed: {e}")

    def _locate_start_index(self, host: str, port: int) -> int:
        """定位起始索引：按解析后的 (host, port) 元组比对，而非原始字符串。

        端口前导零在解析后归一(08080 -> 8080)，因此入参与列表项能正确匹配；
        找不到时返回 0，从列表首项开始轮询。
        """
        for i, entry in enumerate(self.host_list or []):
            _h, _p = parse_host_port(entry)
            if _h == host and _p == port:
                return i
        return 0

    def _fire_host_list_get(self, reason: str) -> None:
        """所有 host 都试过仍失败，触发云端重新拉取 host_list"""
        VLog.info(_TAG, f"[reconnect_loop][{reason}] all hosts tried, fire {EVENT_VHOME_HOST_LIST_GET}")
        if self.hass is not None:
            self.hass.bus.fire(EVENT_VHOME_HOST_LIST_GET, {})

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