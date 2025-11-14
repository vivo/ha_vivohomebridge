"""
 Copyright 2024 vivo Mobile Communication Co., Ltd.
 Licensed under the Apache License, Version 2.0 (the "License");

    http://www.apache.org/licenses/LICENSE-2.0
"""

import ctypes
import os
import platform
import re
import shlex
import subprocess
import sys
import threading
import json
from ctypes import c_char_p, c_void_p, c_int, c_char, c_int, POINTER
from pathlib import Path
from typing import Callable, Optional, Tuple
import logging

_LOGGER = logging.getLogger("py_vhome")
system = platform.system()
machine = platform.machine()
LIBVERSION = "1.1.1"
"""
检测机器架构

Args:
 machine (str): 机器的架构名称

Returns:
 str: 规范化的机器架构名称
"""
def detect_arch(machine: str) -> str:
    m = machine.lower()
    if m in ("x86_64", "amd64"):
        return "x86_64"
    if m in ("aarch64", "arm64"):
        return "aarch64"
    if m in ("armv7l", "armv7", "armhf"):
        return "armv7"
    if m in ("armv6l", "armv6", "armel"):
        return "armv6"
    if m in ("i386", "i686", "x86"):
        return "x86"
    return m

def safe_process_run(cmd: str, timeout: float = 2.0) -> str:
    
    try:
        mproc = subprocess.run(
            shlex.split(cmd),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=timeout,
            check=False,
            text=True,
        )
        return mproc.stdout or ""
    except Exception as e:
        _LOGGER.error(f"Failed run process: {e}")
        return ""

def detect_libc() -> str:
    
    out = safe_process_run("ldd --version")
    s = out.lower()
    if "musl" in s:
        return "musl"
    if "glibc" in s or "gnu c library" in s or "gnu libc" in s:
        return "glibc"
    
    lname, lver = platform.libc_ver()
    if lname:        
        lname_l = lname.lower()
        if "glibc" in lname_l or "gnu" in lname_l:
            return "glibc"
        if "musl" in lname_l:
            return "musl"
    
    linker_candidates = [
        "/lib/ld-musl-x86_64.so.1",
        "/lib/ld-musl-aarch64.so.1",
        "/lib/ld-musl-armhf.so.1",
        "/lib/ld-musl-arm.so.1",
        "/lib64/ld-linux-x86-64.so.2",
        "/lib/x86_64-linux-gnu/ld-linux-x86-64.so.2",
        "/lib/ld-linux-aarch64.so.1",
        "/lib/aarch64-linux-gnu/ld-linux-aarch64.so.1",
    ]
    for p in linker_candidates:
        if Path(p).exists():
            return "musl" if "musl" in p else "glibc"

    return "unknown"  

def detect_platform() -> Tuple[str, str, Optional[str]]:
    sysplat = sys.platform
    arch = detect_arch(machine)

    if sysplat.startswith("win"):
        return ("windows", arch, None)
    elif sysplat.startswith("linux"):
        libc = detect_libc()
        return ("linux", arch, libc)
    else:
        return (sysplat, arch, libc)

def build_library_filename(base: str, os_name: str, arch: str, libc: Optional[str], libVersion: str) -> str:
    if os_name == "windows":
        # libvhome_windows_x86_64_1.0.0.dll
        return f"{base}_windows_{arch}_{libVersion}.dll"
    elif os_name == "linux":
        if arch == "aarch64":
            # libvhome_linux_aarch64_1.0.0.so
            return f"{base}_linux_musl_aarch64_{libVersion}.so"
        elif arch == "armv7":
            # libvhome_linux_arm7_1.0.0.so
            return f"{base}_linux_musl_armv7_{libVersion}.so"
        elif arch == "armv6":
            # libvhome_linux_arm6_1.0.0.so
            return f"{base}_linux_musl_armv6_{libVersion}.so"
        else:
            libc_tag = libc if libc in ("glibc", "musl") else "unknown"
            #libvhome_linux_glibc_x86_64_1.0.0.so libvhome_linux_musl_x86_64_1.0.0.so
            return f"{base}_linux_{libc_tag}_{arch}_{libVersion}.so"
    else:
        return f"{base}_{os_name}_{arch}_{libVersion}.so"

def lib_name(base_name: str, libVersion: str)-> str:
    os_name, arch, libc = detect_platform()
    return build_library_filename(base_name, os_name, arch, libc, libVersion)


libpath = (
    os.path.dirname(os.path.abspath(__file__)) + "/" + lib_name("libvhome", LIBVERSION )
)

try:
    vhome_lib = ctypes.CDLL(libpath)
except OSError as e:
    _LOGGER.error(f"Failed to load library: {e}")
    raise Exception("Failed to load library: {}".format(e))

"""void vhome_init(char *url)"""
vhome_lib.vhome_init.restype = None
vhome_lib.vhome_init.argtypes = [c_void_p]
"""void vhome_deinit(void)"""
vhome_lib.vhome_deinit.restype = None
vhome_lib.vhome_deinit.argtypes = []
"""void vhome_memory_free( void* pData )"""
vhome_lib.vhome_memory_free.argtypes = [c_void_p]
"""char* vhome_get_bind_code_by_mac( char* mac )"""
vhome_lib.vhome_get_bind_code_by_mac.restype = POINTER(c_char)
vhome_lib.vhome_get_bind_code_by_mac.argtypes = [c_char_p]
"""char* vhome_bind( char* bcode, char* mac )"""
vhome_lib.vhome_bind.restype = POINTER(c_char)
vhome_lib.vhome_bind.argtypes = [c_char_p, c_char_p, c_char_p]
"""char* vhome_sub_devices_register( char* bcode,char* dn,char* mac,char* sub_devices )"""
vhome_lib.vhome_sub_devices_register.restype = POINTER(c_char)
vhome_lib.vhome_sub_devices_register.argtypes = [c_char_p, c_char_p, c_char_p, c_char_p]
"""int vhome_data_upload( char* dn,char* data )"""
vhome_lib.vhome_data_upload.restype = ctypes.c_int
vhome_lib.vhome_data_upload.argtypes = [c_char_p, c_char_p]
"""int vhome_connect( char* ip,int port,char*bcode,char* dn )"""
vhome_lib.vhome_connect.restype = ctypes.c_int
vhome_lib.vhome_connect.argtypes = [c_char_p, c_int, c_char_p, c_char_p]
"""int vhome_disconnect( void )"""
vhome_lib.vhome_disconnect.restype = ctypes.c_int
vhome_lib.vhome_disconnect.argtypes = []
"""char* data_to_python(void)"""
vhome_lib.data_to_python.restype = POINTER(c_char)
vhome_lib.data_to_python.argtypes = []
"""char* vhome_so_version(void)"""
vhome_lib.vhome_so_version.restype = POINTER(c_char)
vhome_lib.vhome_so_version.argtypes = []
"""char* vhome_so_build_time(void)"""
vhome_lib.vhome_so_build_time.restype = POINTER(c_char)
vhome_lib.vhome_so_build_time.argtypes = []

"""void vhome_network_shakehand_task_start(void);"""
vhome_lib.vhome_network_shakehand_task_start.restype = None
vhome_lib.vhome_network_shakehand_task_start.argtypes = []
"""void vhome_network_shakehand_task_stop(void);"""
vhome_lib.vhome_network_shakehand_task_stop.restype = None
vhome_lib.vhome_network_shakehand_task_stop.argtypes = []
"""int vhome_send_bind_code_to_app( char *bindCode );"""
vhome_lib.vhome_send_bind_code_to_app.restype = ctypes.c_int
vhome_lib.vhome_send_bind_code_to_app.argtypes = [c_char_p]
"""int get_local_net_target_port(void);"""
vhome_lib.get_local_net_target_port.restype = ctypes.c_int
vhome_lib.get_local_net_target_port.argtypes = []


class VHome:
    def __init__(
        self,
        url: str,
        on_state: Optional[Callable[[dict], None]] = None,
        on_data_received: Optional[Callable[[dict], None]] = None,
        on_local_event: Optional[Callable[[str], None]] = None,
    ):
        """
        初始化方法

        Args:
         on_state (Optional[Callable[[dict], None]]): 状态变化时的回调函数，接收一个字典作为参数
         on_data_received (Optional[Callable[[dict], None]]): 数据接收时的回调函数，接收一个字典作为参数

        Returns:
         None
        """
        _LOGGER.info(f"VHome work on {system}+{machine}")
        self._on_state = (
            on_state if callable(on_state) else self._default_on_state_callback
        )
        self._on_data = (
            on_data_received
            if callable(on_data_received)
            else self._default_on_data_received_callback
        )
        self._on_local_event = (
            on_local_event
            if callable(on_local_event)
            else self._default_on_local_event_callback
        )
        vhome_lib.vhome_init(url.encode("utf-8"))
        self.start_data_listener()

    def start_data_listener(self):
        thread = threading.Thread(target=self._data_from_c_to_python)
        thread.daemon = True  # 设置为守护线程，以便在主线程结束时自动退出
        thread.start()

    @ctypes.CFUNCTYPE(None, ctypes.c_char_p)
    def log_debug_callback(msg_ptr):
        msg = msg_ptr.decode("utf-8")
        _LOGGER.debug("[Native] %s", msg)

    @ctypes.CFUNCTYPE(None, ctypes.c_char_p)
    def log_info_callback(msg_ptr):
        msg = msg_ptr.decode("utf-8")
        _LOGGER.info("[Native] %s", msg)

    @ctypes.CFUNCTYPE(None, ctypes.c_char_p)
    def log_warning_callback(msg_ptr):
        msg = msg_ptr.decode("utf-8")
        _LOGGER.warning("[Native] %s", msg)

    @ctypes.CFUNCTYPE(None, ctypes.c_char_p)
    def log_error_callback(msg_ptr):
        msg = msg_ptr.decode("utf-8")
        _LOGGER.error("[Native] %s", msg)

    """
    处理默认状态回调

    Args:
     state (dict): 状态信息字典

    Returns:
     None
    """

    def _default_on_state_callback(state: dict):
        """默认回调处理"""
        _LOGGER.warning(f"[WARN] 未注册的回调被触发，参数: {state}")

    def _default_on_data_received_callback(data: dict):
        """默认回调处理"""
        _LOGGER.warning(f"[WARN] 未注册的回调被触发，参数: {data}")

    def _default_on_local_event_callback(state: dict):
        """默认回调处理"""
        _LOGGER.warning(f"[WARN] 未注册的回调被触发，参数: {state}")

    def _data_from_c_to_python(self):
        """获取从C传过来的数据"""
        _LOGGER.info("开始监听C传过来的数据:_data_from_c_to_python")
        while True:
            result = vhome_lib.data_to_python()
            if result:
                result_str = ctypes.cast(result, c_char_p).value.decode("utf-8")
                vhome_lib.vhome_memory_free(result)
                # _LOGGER.info(f"data from so: {result_str}")
                result_dict = json.loads(result_str)
                if result_dict["type"] == 0:
                    del result_dict["type"]
                    self._on_state(result_dict)
                elif result_dict["type"] == 1:
                    del result_dict["type"]
                    self._on_data(result_dict)
                elif result_dict["type"] == 2:
                    # 配网数据
                    _LOGGER.info(f"client sharkhand success : {result_dict}")
                    self._on_local_event(result_dict)

    def _get_bcode(self, mac: str) -> dict:
        """获取绑定码"""
        result_dict = {}
        result = vhome_lib.vhome_get_bind_code_by_mac(mac.encode("utf-8"))
        if result:
            result_str = ctypes.cast(result, c_char_p).value.decode("utf-8")
            _LOGGER.info(f"[INFO] 获取绑定码结果 : {result_str}")
            vhome_lib.vhome_memory_free(result)
            result_dict = json.loads(result_str)
        return result_dict

    def _bind(self, bcode: str, mac: str, en: str) -> dict:
        """设备绑定"""
        result_dict = {}
        result = vhome_lib.vhome_bind(
            bcode.encode("utf-8"), mac.encode("utf-8"), en.encode("utf-8")
        )
        if result:
            result_str = ctypes.cast(result, c_char_p).value.decode("utf-8")
            _LOGGER.info(f"设备绑定结果 : {result_str}")
            vhome_lib.vhome_memory_free(result)
            result_dict = json.loads(result_str)
        return result_dict

    def _sub_devices_register(
        self, bcode: str, dn: str, mac: str, sub_devices: list[dict]
    ) -> dict:
        result_dict = {}
        try:
            json_sub_devices = json.dumps(sub_devices)
            result = vhome_lib.vhome_sub_devices_register(
                bcode.encode("utf-8"),
                dn.encode("utf-8"),
                mac.encode("utf-8"),
                json_sub_devices.encode("utf-8"),
            )
        except Exception as e:
            _LOGGER.warning( f"json_sub_devices fail <{e}>")
            return result_dict
            
        if result:
            result_str = ctypes.cast(result, c_char_p).value.decode("utf-8")
            _LOGGER.info(f"子设备注册结果 : {result_str}")
            vhome_lib.vhome_memory_free(result)
            result_dict = json.loads(result_str)
        else:
            _LOGGER.warning("Sub_devices_register result is Null")
        return result_dict

    def _connect(self, host: str, port: int, dn: str, user_code: str) -> int:
        result = 0
        result = vhome_lib.vhome_connect(
            host.encode("utf-8"), port, user_code.encode("utf-8"), dn.encode("utf-8")
        )
        return result

    def _disconnect(self, dn: str) -> int:
        result = 0
        result = vhome_lib.vhome_disconnect()
        return result

    def _data_upload(self, dn: str, data: list[dict]) -> int:
        result = 0
        result = vhome_lib.vhome_data_upload(
            dn.encode("utf-8"), json.dumps(data).encode("utf-8")
        )
        return result

    def _network_shakehand_task_start(self):
        vhome_lib.vhome_network_shakehand_task_start()

    def _network_shakehand_task_stop(self):
        vhome_lib.vhome_network_shakehand_task_stop()

    def _send_bind_code_to_app(self, bindCode: dict) -> int:
        _LOGGER.debug(f"_send_bind_code_to_app:{bindCode}")
        try:
            json_bindCode = json.dumps(bindCode)
            return vhome_lib.vhome_send_bind_code_to_app(
            json_bindCode.encode("utf-8")
        )
        except Exception as e:
            _LOGGER.warning( f"<json error: {e}>") 
            return -1


    async def async_get_bcode(self, mac: str) -> dict:
        """获取绑定码
        Args:
            mac: 网卡物理地址(mac)
        """
        return self._get_bcode(mac)

    async def async_bind(self, bcode: str, mac: str, en: str) -> dict:
        """绑定设备.

        Args:
            bcode: 绑定码(bcode)
            mac: 网卡物理地址(mac)

        Returns:
            绑定设备结果

        """
        return self._bind(bcode, mac, en)

    async def async_send_bind_code_to_app(self, bcode: dict) -> int:
        return self._send_bind_code_to_app(bcode)

    async def async_sub_devices_register(
        self, bcode: str, dn: str, mac: str, sub_devices: list[dict]
    ) -> dict:
        """子设备注册"""
        result_devices = []
        register_sub_device_result = self._sub_devices_register(
            bcode, dn, mac, sub_devices
        )
        if (
            register_sub_device_result is None
            or register_sub_device_result.get("code", None) is None
        ):
            return {"fail": result_devices, "code": 6000}
        if register_sub_device_result["code"] == 10000:
            for success_sub_device in register_sub_device_result["data"]["succ"]:
                result_devices.append(
                    {
                        "logicMac": success_sub_device["logicMac"],
                        "dn": success_sub_device["pky"] + success_sub_device["dn"],
                    }
                )
            return {"success": result_devices, "code": 0}
        else:
            return {
                "fail": result_devices,
                "code": register_sub_device_result.get("code", 6001),
            }

    async def async_data_upload(self, dn: str, data: list[dict]) -> int:
        return self._data_upload(dn, data)

    async def async_connect(self, host: str, port: int, dn: str, user_code: str) -> int:
        """
        连接到 VHome 服务

        Args:
         dn (str): 设备的唯一标识符

        Returns:
         0:接口调用成功，最终连接成功需要通过状态回调通知获取:{'state': 1, 'connect_result': 0}
         其他:失败
        """
        return self._connect(host, port, dn, user_code)

    async def async_disconnect(self, dn: str) -> int:
        """
        断开与 VHome 服务的连接
        Args:
         dn (str): 设备的唯一标识符
        """
        return self._disconnect(dn)

    def version(self) -> str:
        c_type_result = vhome_lib.vhome_so_version()
        result_str = ""
        if c_type_result:
            result_str = ctypes.cast(c_type_result, c_char_p).value.decode("utf-8")
        return result_str

    def build_time(self) -> str:
        c_type_result = vhome_lib.vhome_so_build_time()
        result_str = ""
        if c_type_result:
            result_str = ctypes.cast(c_type_result, c_char_p).value.decode("utf-8")
        return result_str

    def get_local_net_target_port(self) -> int:
        return vhome_lib.get_local_net_target_port()

    async def network_shakehand_task_start(self) -> None:
        _LOGGER.warning("Start network_shakehand ... ")
        self._network_shakehand_task_start()
        return

    async def network_shakehand_task_stop(self) -> None:
        _LOGGER.warning("Stop network_shakehand ... ")
        self._network_shakehand_task_stop()
