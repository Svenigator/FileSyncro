# src/peer_manager.py
import asyncio
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional
import aiohttp


@dataclass
class Peer:
    name: str
    ip: str
    port: int = 5757
    reachable: bool = True
    consecutive_failures: int = 0
    group: str | None = None
    known_groups: list[str] = field(default_factory=list)


class PeerManager:
    def __init__(self, sync_dir: Path, on_peer_status_changed: Optional[Callable[["Peer"], None]] = None):
        self.sync_dir = sync_dir
        self.on_peer_status_changed = on_peer_status_changed
        self._peers: dict[str, Peer] = {}
        self._my_group: str | None = None

    @property
    def peers(self) -> list[Peer]:
        return list(self._peers.values())

    def add_peer(self, peer: Peer) -> None:
        self._peers[peer.name] = peer

    def remove_peer(self, name: str) -> None:
        self._peers.pop(name, None)

    def set_my_group(self, name: str | None) -> None:
        self._my_group = name

    @property
    def active_peers(self) -> list[Peer]:
        if self._my_group is None:
            return self.peers
        return [p for p in self.peers if p.group == self._my_group]

    def _url(self, peer: Peer, path: str) -> str:
        return f"http://{peer.ip}:{peer.port}{path}"

    def _mark_unreachable(self, peer: Peer) -> None:
        peer.reachable = False
        if self.on_peer_status_changed:
            self.on_peer_status_changed(peer)

    async def _fetch_peer_info(self, peer: Peer, session: aiohttp.ClientSession) -> None:
        try:
            async with session.get(
                self._url(peer, "/info"),
                timeout=aiohttp.ClientTimeout(total=3),
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    peer.group = data.get("group")
                    peer.known_groups = data.get("groups", [])
        except Exception:
            pass

    async def send_file(self, rel_path: str) -> dict[str, bool]:
        file_path = self.sync_dir / rel_path
        if not file_path.exists():
            return {}
        data = file_path.read_bytes()
        ts = file_path.stat().st_mtime
        results: dict[str, bool] = {}
        async with aiohttp.ClientSession() as session:
            for peer in self.active_peers:
                try:
                    async with session.put(
                        self._url(peer, f"/file/{rel_path}"),
                        data=data,
                        headers={"X-Timestamp": str(ts)},
                        timeout=aiohttp.ClientTimeout(total=30)
                    ) as resp:
                        peer.reachable = True
                        results[peer.name] = resp.status in (200, 409)
                except Exception:
                    results[peer.name] = False
                    self._mark_unreachable(peer)
        return results

    async def delete_file(self, rel_path: str) -> dict[str, bool]:
        results: dict[str, bool] = {}
        async with aiohttp.ClientSession() as session:
            for peer in self.active_peers:
                try:
                    async with session.delete(
                        self._url(peer, f"/file/{rel_path}"),
                        timeout=aiohttp.ClientTimeout(total=10)
                    ) as resp:
                        peer.reachable = True
                        results[peer.name] = resp.status == 200
                except Exception:
                    results[peer.name] = False
                    self._mark_unreachable(peer)
        return results

    async def get_peer_files(self, peer: Peer) -> dict[str, float]:
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(
                    self._url(peer, "/files"),
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    if resp.status == 200:
                        peer.reachable = True
                        return await resp.json()
            except Exception:
                self._mark_unreachable(peer)
        return {}

    async def ping(self, peer: Peer) -> bool:
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(
                    self._url(peer, "/files"),
                    timeout=aiohttp.ClientTimeout(total=3),
                ) as resp:
                    reachable = resp.status == 200
                    if peer.reachable != reachable:
                        peer.reachable = reachable
                        if self.on_peer_status_changed:
                            self.on_peer_status_changed(peer)
                    if reachable:
                        await self._fetch_peer_info(peer, session)
                    return reachable
            except Exception:
                if peer.reachable:
                    self._mark_unreachable(peer)
                return False

    async def ping_all(self) -> list[str]:
        removed: list[str] = []
        # Health-check ALL known peers regardless of active group filter
        for name, peer in list(self._peers.items()):
            reachable = await self.ping(peer)
            if reachable:
                peer.consecutive_failures = 0
            else:
                peer.consecutive_failures += 1
                if peer.consecutive_failures >= 3:
                    self.remove_peer(name)
                    removed.append(name)
        return removed

    async def sync_with_all(self) -> None:
        if not self.sync_dir.exists():
            return
        local_files: dict[str, float] = {}
        for root, _dirs, files in os.walk(self.sync_dir, onerror=lambda _: None):
            for name in files:
                f = Path(root) / name
                rel = str(f.relative_to(self.sync_dir)).replace('\\', '/')
                local_files[rel] = f.stat().st_mtime

        for peer in self.active_peers:
            remote_files = await self.get_peer_files(peer)
            for rel_path, local_ts in local_files.items():
                remote_ts = remote_files.get(rel_path)
                if remote_ts is None or local_ts > remote_ts + 1.0:
                    await self._push_to_peer(peer, rel_path)

    async def _push_to_peer(self, peer: Peer, rel_path: str) -> None:
        file_path = self.sync_dir / rel_path
        if not file_path.exists():
            return
        data = file_path.read_bytes()
        ts = file_path.stat().st_mtime
        async with aiohttp.ClientSession() as session:
            try:
                async with session.put(
                    self._url(peer, f"/file/{rel_path}"),
                    data=data,
                    headers={"X-Timestamp": str(ts)},
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as resp:
                    peer.reachable = True
            except Exception:
                self._mark_unreachable(peer)
