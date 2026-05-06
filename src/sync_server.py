# src/sync_server.py
import asyncio
import os
from pathlib import Path
from aiohttp import web


class SyncServer:
    PORT = 5757

    def __init__(self, sync_dir: Path, on_conflict=None, on_before_delete=None):
        self.sync_dir = sync_dir
        self.on_conflict = on_conflict
        self.on_before_delete = on_before_delete
        self._app = web.Application()
        self._app.router.add_put('/file/{path:.*}', self._handle_put)
        self._app.router.add_delete('/file/{path:.*}', self._handle_delete)
        self._app.router.add_get('/files', self._handle_list)
        self._runner = None

    async def _handle_put(self, request: web.Request) -> web.Response:
        rel_path = request.match_info['path']
        if '..' in rel_path or rel_path.startswith('/') or rel_path.startswith('\\'):
            return web.Response(status=400, text='invalid path')

        remote_ts = float(request.headers.get('X-Timestamp', '0'))
        data = await request.read()
        file_path = self.sync_dir / rel_path

        if file_path.exists():
            local_ts = file_path.stat().st_mtime
            if abs(local_ts - remote_ts) < 1.0:
                return web.Response(status=200, text='unchanged')
            if self.on_conflict:
                loop = asyncio.get_running_loop()
                future: asyncio.Future = loop.create_future()
                self.on_conflict(rel_path, local_ts, remote_ts, data, future)
                accept = await future
                if not accept:
                    return web.Response(status=409, text='conflict rejected')

        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_bytes(data)
        os.utime(file_path, (remote_ts, remote_ts))
        return web.Response(status=200, text='ok')

    async def _handle_delete(self, request: web.Request) -> web.Response:
        rel_path = request.match_info['path']
        if '..' in rel_path or rel_path.startswith('/') or rel_path.startswith('\\'):
            return web.Response(status=400, text='invalid path')

        file_path = self.sync_dir / rel_path
        if self.on_before_delete:
            self.on_before_delete(rel_path)
        if file_path.exists():
            file_path.unlink()
        return web.Response(status=200)

    async def _handle_list(self, request: web.Request) -> web.Response:
        files: dict[str, float] = {}
        if self.sync_dir.exists():
            for f in self.sync_dir.rglob('*'):
                if f.is_file():
                    rel = str(f.relative_to(self.sync_dir)).replace('\\', '/')
                    files[rel] = f.stat().st_mtime
        return web.json_response(files)

    async def start(self) -> None:
        self._runner = web.AppRunner(self._app)
        await self._runner.setup()
        site = web.TCPSite(self._runner, '0.0.0.0', self.PORT)
        await site.start()

    async def stop(self) -> None:
        if self._runner:
            await self._runner.cleanup()
