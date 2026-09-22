"""
 Copyright 2024 vivo Mobile Communication Co., Ltd.
 Licensed under the Apache License, Version 2.0 (the "License");

    http://www.apache.org/licenses/LICENSE-2.0
"""

import asyncio
import ctypes
import os
import platform
import re
import shlex
import subprocess
import sys
import threading
import queue
import json
from concurrent.futures import ThreadPoolExecutor
from ctypes import c_char_p, c_void_p, c_int, c_char, c_int, POINTER
from pathlib import Path
from typing import Callable, Optional, Tuple
import logging

_LOGGER = logging.getLogger("py_vhome")
system = platform.system()
machine = platform.machine()
LIBVERSION = "1.1.2"

# C 调用专用单工作线程池。
_c_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="vhome_c")
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
"""char* vhome_access_host_get( char* dn )"""
vhome_lib.vhome_access_host_get.restype = POINTER(c_char)
vhome_lib.vhome_access_host_get.argtypes = [c_char_p]
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

"""void vhome_register_data_callback(void (*cb)(const char* data));"""
DATA_CALLBACK_TYPE = ctypes.CFUNCTYPE(None, ctypes.c_char_p)
vhome_lib.vhome_register_data_callback.restype = None
vhome_lib.vhome_register_data_callback.argtypes = [DATA_CALLBACK_TYPE]


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
        # C->Python 数据队列。用实例属性而非模块级全局，避免多实例/模块重载
        # 时 C 回调与消费线程引用到不同队列
        self._msg_queue = queue.Queue()
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

        # 注册 C->Python 数据回调。self._c_callback 必须保存为实例属性，
        # 否则 CFUNCTYPE 对象被 GC 后 C 侧会调用已失效的函数指针
        def _on_c_data_callback(data_ptr):
            self._msg_queue.put(data_ptr)

        self._c_callback = DATA_CALLBACK_TYPE(_on_c_data_callback)
        vhome_lib.vhome_register_data_callback(self._c_callback)

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
        """消费线程: 从队列取出 C 侧回调投递的数据并分发"""
        _LOGGER.info("开始监听C传过来的数据:_data_from_c_to_python")
        while True:
            try:
                # 阻塞等待 C 侧回调 put 进来的 bytes
                result = self._msg_queue.get()
            except Exception as e:
                _LOGGER.error(f"msg_queue get error: {e}")
                continue
            if not result:
                continue
            try:
                self._dispatch_c_data(result)
            except Exception:
                # 任何一条消息的分发异常都不能让消费线程退出，否则后续
                # 所有 C->Python 数据都会被静默丢弃
                _LOGGER.exception("dispatch c data failed, skip this message")

    def _dispatch_c_data(self, result):
        """解析并按 type 分发。result 是 ctypes 从 c_char_p 拷贝出的 bytes"""
        result_str = result.decode("utf-8")
        _LOGGER.info(f"data from c-so: {result_str}")
        try:
            result_dict = json.loads(result_str)
        except Exception as e:
            _LOGGER.error(f"json parse error: {e}")
            return
        msg_type = result_dict.get("type")
        if msg_type == 0:
            del result_dict["type"]
            self._on_state(result_dict)
        elif msg_type == 1:
            del result_dict["type"]
            self._on_data(result_dict)
        elif msg_type == 2:
            # 配网数据。_on_local_event 是同步函数，内部自行通过
            # hass.loop.call_soon_threadsafe 调度到事件循环，这里直接调用
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


    async def _run_c(self, func, *args):
        """把阻塞的 C 调用投递到专用单 worker 线程池执行。

        所有 async_* 包装都必须经此调用, 不要直接调 self._xxx:
        直接调会在事件循环线程上阻塞 HA
        """
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(_c_executor, func, *args)

    async def async_get_bcode(self, mac: str) -> dict:
        """获取绑定码
        Args:
            mac: 网卡物理地址(mac)
        """
        return await self._run_c(self._get_bcode, mac)

    async def async_bind(self, bcode: str, mac: str, en: str) -> dict:
        """绑定设备.

        Args:
            bcode: 绑定码(bcode)
            mac: 网卡物理地址(mac)

        Returns:
            绑定设备结果

        """
        return await self._run_c(self._bind, bcode, mac, en)

    def _access_host_get_sync(self, dn: str) -> dict:
        '''同步阻塞实现: 供 executor 调用, 不要在事件循环里直接调。

        C 侧 vhome_access_host_get 走 HTTP 请求, 超时 BIND_RECEIVE_TIME_OUT=10s,
        整个调用期间会阻塞所在线程。指针的获取与释放在同一线程内完成。
        '''
        result_dict = {}
        result = vhome_lib.vhome_access_host_get(dn.encode("utf-8"))
        if result:
            try:
                result_str = ctypes.cast(result, c_char_p).value.decode("utf-8")
                _LOGGER.info(f"access host get result : {result_str}")
                result_dict = json.loads(result_str)
            except Exception as e:
                _LOGGER.error(f"access host get parse error: {e}")
            finally:
                vhome_lib.vhome_memory_free(result)
        return result_dict

    async def async_access_host_get(self, dn: str) -> dict:
        '''获取接入点列表
        Args:
            dn: device_name

        Result:
            {'code': 10000, 'data': {'ntp': '1789907882855', 'ip': ['AAA.AAA.AAA.AAA:XXXXX', 'BBB.BBB.BBB.BBB:XXXXX']}}

        调用方 async_access_host_get_task 是无限重试循环, 每次最长阻塞 10s,
        必须走 executor 避免卡住 HA 事件循环。
        '''
        return await self._run_c(self._access_host_get_sync, dn)

    async def async_send_bind_code_to_app(self, bcode: dict) -> int:
        return await self._run_c(self._send_bind_code_to_app, bcode)

    async def async_sub_devices_register(
        self, bcode: str, dn: str, mac: str, sub_devices: list[dict]
    ) -> dict:
        """子设备注册"""
        result_devices = []
        register_sub_device_result = await self._run_c(
            self._sub_devices_register, bcode, dn, mac, sub_devices
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
        return await self._run_c(self._data_upload, dn, data)

    async def async_connect(self, host: str, port: int, dn: str, user_code: str) -> int:
        """
        连接到 VHome 服务

        Args:
         dn (str): 设备的唯一标识符

        Returns:
         0:接口调用成功，最终连接成功需要通过状态回调通知获取:{'state': 1, 'connect_result': 0}
         其他:失败

        注意: C 侧 mbedtls_net_connect 未设超时, 连不可达地址时阻塞可达
        约 127s(Linux tcp_syn_retries 默认 6), 必须走 executor。
        """
        return await self._run_c(self._connect, host, port, dn, user_code)

    async def async_disconnect(self, dn: str) -> int:
        """
        断开与 VHome 服务的连接
        Args:
         dn (str): 设备的唯一标识符
        """
        return await self._run_c(self._disconnect, dn)

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
        await self._run_c(self._network_shakehand_task_start)
        return

    async def network_shakehand_task_stop(self) -> None:
        # 本身不阻塞(pthread_cancel 不 join), 但操作的 netcfg 全局
        # (taskHandle/tcpClientFd/net_task_running)与 send_bind_code_to_app
        # 共享, 走同一 executor 以保持串行
        _LOGGER.warning("Stop network_shakehand ... ")
        await self._run_c(self._network_shakehand_task_stop)
