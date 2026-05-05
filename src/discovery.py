# src/discovery.py
import socket
import asyncio
from typing import Callable, Optional
from zeroconf import ServiceBrowser, ServiceInfo, Zeroconf
from zeroconf.asyncio import AsyncZeroconf


SERVICE_TYPE = "_filesyncro._tcp.local."


class Discovery:
    def __init__(
        self,
        name: str,
        port: int,
        on_peer_found: Optional[Callable[[str, str, int], None]],
        on_peer_lost: Optional[Callable[[str], None]],
    ):
        self._name = name
        self._port = port
        self._on_peer_found = on_peer_found
        self._on_peer_lost = on_peer_lost
        self._azc: Optional[AsyncZeroconf] = None
        self._browser: Optional[ServiceBrowser] = None
        self._info: Optional[ServiceInfo] = None

    def _local_ip(self) -> str:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]

    def _build_service_info(self, ip: str) -> ServiceInfo:
        return ServiceInfo(
            type_=SERVICE_TYPE,
            name=f"{self._name}.{SERVICE_TYPE}",
            addresses=[socket.inet_aton(ip)],
            port=self._port,
            properties={"name": self._name},
        )

    async def start(self) -> None:
        self._azc = AsyncZeroconf()
        ip = self._local_ip()
        self._info = self._build_service_info(ip)
        await self._azc.async_register_service(self._info)
        self._browser = ServiceBrowser(
            self._azc.zeroconf, SERVICE_TYPE, handlers=[self._handle_state_change]
        )

    async def stop(self) -> None:
        if self._azc:
            if self._info:
                await self._azc.async_unregister_service(self._info)
            await self._azc.async_close()

    def _handle_state_change(self, zeroconf: Zeroconf, service_type: str, name: str, state_change) -> None:
        from zeroconf import ServiceStateChange
        if state_change == ServiceStateChange.Added:
            info = zeroconf.get_service_info(service_type, name)
            if info and info.name != self._info.name:
                ip = socket.inet_ntoa(info.addresses[0])
                peer_name = info.properties.get(b"name", b"unknown").decode()
                if self._on_peer_found:
                    self._on_peer_found(peer_name, ip, info.port)
        elif state_change == ServiceStateChange.Removed:
            peer_name = name.replace(f".{SERVICE_TYPE}", "")
            if self._on_peer_lost:
                self._on_peer_lost(peer_name)
