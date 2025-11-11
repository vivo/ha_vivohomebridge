"""
 Copyright 2024 vivo Mobile Communication Co., Ltd.
 Licensed under the Apache License, Version 2.0 (the "License");

    http://www.apache.org/licenses/LICENSE-2.0
"""
import asyncio

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

    def __init__(self, vhome):
        self._vhome = vhome
        self._stop_event = asyncio.Event()
        self._reconnect_task = None

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
        if self._reconnect_task is None or (self._reconnect_task.done() and self._stop_event.is_set()):
            try:
                self._reconnect_task = asyncio.create_task(self._reconnect_loop(host, port, dn, user_code, reason))
            except Exception as e:
                VLog.error(_TAG, f"Failed to create reconnect task: {e}")
        else:
            VLog.warning(_TAG, f"[start_reconnect]:reconnect task already running when {reason}")

    async def _reconnect_loop(self, host, port, dn, user_code, reason) -> None:
        while not self._stop_event.is_set():
            try:
                VLog.info(_TAG, f"[reconnect_loop][{reason}] reconnect after 5 second")
                await asyncio.sleep(5)
            except asyncio.CancelledError as err:
                VLog.info(_TAG, f"[reconnect_loop] cancel when {reason}:{err}")
                break

            VLog.info(_TAG, f"[reconnect_loop][{reason}] reconnecting...")
            try:
                connect_result = await self._vhome.async_connect(host, port, dn, user_code)
                if connect_result == 0:
                    VLog.info(_TAG, f"[reconnect_loop][{reason} reconnected")
                    await self.stop_reconnect("reconnected")
                    break
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
