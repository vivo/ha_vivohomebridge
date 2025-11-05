import socket
from typing import List
import netifaces
import psutil
import asyncio
import random
from homeassistant.helpers.network import get_url
from zeroconf import NonUniqueNameException
from zeroconf.asyncio import AsyncServiceInfo, AsyncZeroconf

from homeassistant.core import HomeAssistant
from homeassistant.components import zeroconf as ha_zeroconf
from .v_utils.vlog import VLog
from .const import (
    VIVO_HA_BRIDGE_PK,
    LOCAL_DISCOVERY_SERVICE_NAME,
)
# from .device_manager import DeviceManager

_TAG = "LocalService"


class VLocalService:
    def __init__(self, hass: HomeAssistant, name: str, ver: str, mac: str) -> None:
        """Initialize the service info."""
        if name is None:
            raise ValueError("The 'name' parameter cannot be None.")
        if mac is None:
            raise ValueError("The 'mac' parameter cannot be None.")
        self.isRunning = False
        self.hass = hass
        _ips = self._get_all_local_ips()
        # _ips = network.async_get_announce_addresses(hass)
        VLog.info(_TAG, f"IPs {_ips}")

        if not _ips:
            VLog.warning(
                _TAG, "The valid IP was not obtained, skipping mDNS registration."
            )
            return
        mac_server = mac.replace(":", "")
        self._type = "_vhome._tcp.local."
        self._name = LOCAL_DISCOVERY_SERVICE_NAME + "-" + mac_server + "." + self._type
        self._ips = _ips
        self._port = 0
        self._server = LOCAL_DISCOVERY_SERVICE_NAME + "-" + mac_server + ".local."
        self._txt_id = mac
        self._txt_name = name
        self._txt_dn = None
        self._txt_ver = ver
        self._txt_pk = VIVO_HA_BRIDGE_PK
        self._txt_bind = "0"
        self._service: AsyncServiceInfo | None = None

        VLog.info(_TAG, "VLocalService ...")
        return

    def _get_all_local_ips(self) -> list[bytes]:
        ip_list = []
        for iface in netifaces.interfaces():
            addrs = netifaces.ifaddresses(iface)
            VLog.info(_TAG, f"iface:{iface} addrs:{addrs}")
            if (
                iface.startswith("veth")
                or iface.startswith("docker")
                or iface.startswith("br-")
                or iface.startswith("hassio")
            ):
                continue

            if netifaces.AF_INET in addrs:
                for addr in addrs[netifaces.AF_INET]:
                    ip = addr.get("addr")
                    if ip and not ip.startswith("127."):
                        ip_list.append(ip)
        return ip_list

    def config_flag(self, flag: int) -> None:
        """配置是否绑定过，
        0: 表示未绑定
        1: 表示已经绑定了
        2: 表示设备数据无效
        """
        self._txt_bind = flag
        VLog.info(_TAG, f"config_flag:{flag}")


    def config_dn(self, dn: str) -> None:
        self._txt_dn = dn

    def config_ver(self, ver: str) -> None:
        self._txt_ver = ver

    async def sync_update_txt(self) -> None:
        if not self.isRunning or not self._service:
            VLog.warning(_TAG, "Service not running; call sync_start() first.")
            return
        zc = await ha_zeroconf.async_get_instance(self.hass)
        ha_url = get_url(self.hass, prefer_external=False)
        _properties = {
            "id": self._txt_id,
            "name": self._txt_name,
            "ver": self._txt_ver,
            "pk": self._txt_pk,
            "platform": "ha",
            "bind": self._txt_bind,
            "internal_url": ha_url,
        }
        if self._txt_dn:
            _properties["dn"] = self._txt_dn

        updated_service = AsyncServiceInfo(
            type_=self._type,
            name=self._name,
            addresses=[socket.inet_aton(ip) for ip in self._ips],
            port=self._port,
            properties=_properties,
            server=self._server,
        )
        await zc.async_update_service(updated_service)
        self._service = updated_service  # 覆盖本地引用
        VLog.info(
            _TAG, f"Updated mDNS service name: {self._name} ,service:{updated_service}"
        )

    async def sync_start(self, m_port: int) -> None:
        """Start the local discovery process"""
        await self.sync_stop()
        zc = await ha_zeroconf.async_get_instance(self.hass)
        _properties = {}
        ha_url = get_url(self.hass, prefer_external=False)
        if self._txt_dn and len(self._txt_dn) > 0:
            _properties = {
                "id": self._txt_id,
                "name": self._txt_name,
                "dn": self._txt_dn,
                "ver": self._txt_ver,
                "pk": self._txt_pk,
                "platform": "ha",
                "bind": self._txt_bind,
                "internal_url": ha_url,
            }
        else:
            _properties = {
                "id": self._txt_id,
                "name": self._txt_name,
                "ver": self._txt_ver,
                "pk": self._txt_pk,
                "platform": "ha",
                "bind": self._txt_bind,
                "internal_url": ha_url,
            }
        self._port = m_port
        service = AsyncServiceInfo(
            type_=self._type,
            name=self._name,
            addresses=[socket.inet_aton(ip) for ip in self._ips],
            port=self._port,
            properties=_properties,
            server=self._server,
        )

        VLog.info(_TAG, f"internal_url:{ha_url}")
        max_attempts = 5
        attempt = 0
        original_name = self._name
        while attempt < max_attempts:
            if attempt > 0:
                import random

                suffix = f"-{random.randint(1000, 9999)}"
                self._name = original_name.replace(
                    "." + self._type, suffix + "." + self._type
                )
                VLog.info(_TAG, f"Trying with new name: {self._name}")

            service = AsyncServiceInfo(
                type_=self._type,
                name=self._name,
                addresses=[socket.inet_aton(ip) for ip in self._ips],
                port=m_port,
                properties=_properties,
                server=self._server,
            )

            try:
                await zc.async_register_service(service)
                self._service = service
                self.isRunning = True
                VLog.info(
                    _TAG, f"Registered mDNS name: {self._name} ,service:{service}"
                )
                break
            except NonUniqueNameException:
                attempt += 1
                if attempt >= max_attempts:
                    VLog.error(
                        _TAG,
                        f"Failed to register after {max_attempts} attempts with different names",
                    )
            except Exception as e:
                error_message = str(e)
                error_type = type(e).__name__
                import traceback

                error_traceback = traceback.format_exc()
                VLog.warning(_TAG, f"Failed to register service: {e}")
                VLog.error(
                    _TAG,
                    f"Failed to register mDNS service: {error_type} - {error_message}",
                )
                VLog.error(_TAG, f"Error details: {error_traceback}")
                break
        self.isRunning = True

    async def sync_stop(self) -> None:
        """Stop the local discovery service"""
        if self.isRunning is False:
            return
        zc = await ha_zeroconf.async_get_instance(self.hass)

        try:
            await zc.async_unregister_service(self._service)
            VLog.info(_TAG, f"Unregistered service: {self._service.name}")
            await asyncio.sleep(1)
        except Exception as e:
            error_message = str(e)
            error_type = type(e).__name__
            import traceback

            error_traceback = traceback.format_exc()
            VLog.warning(_TAG, f"Failed to unregister service: {e}")
            VLog.error(
                _TAG,
                f"Failed to unregister mDNS service: {error_type} - {error_message}",
            )
            VLog.error(_TAG, f"Error details: {error_traceback}")
        finally:
            self._service = None
            self.isRunning = False
            VLog.info(_TAG, "All mDNS services stopped.")
