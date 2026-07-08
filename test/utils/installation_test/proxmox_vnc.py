# SPDX-FileCopyrightText: 2024-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""
Bridge a Proxmox noVNC (WebSocket) console to a local plain TCP VNC port.

Proxmox exposes a VM's VNC console only via an authenticated WebSocket. This
module authenticates against the Proxmox API with an API token, obtains a VNC
ticket and starts a small TCP<->WebSocket bridge in a background thread, so a
standard VNC client (here: vncdotool/vncautomate) can connect to a local port.

The VNC ticket returned by Proxmox serves two purposes at once: it authorises
the WebSocket handshake *and* it is the RFB password the VNC client must send.
It is short-lived, therefore it is fetched once in :meth:`ProxmoxVNCBridge.start`
and the caller is expected to connect immediately with the returned password.
"""

import asyncio
import json
import logging
import ssl
import threading
import urllib.error
import urllib.parse
import urllib.request
from urllib.parse import quote


try:
    import websockets
except ImportError:  # keep this module importable without websockets installed
    websockets = None


log = logging.getLogger(__name__)

CREDENTIAL_KEYS = (
    "proxmox_host",
    "proxmox_api_user",
    "proxmox_api_token_name",
    "proxmox_api_token_secret",
)


def load_credentials(path: str) -> dict[str, str]:
    """Load and validate a Proxmox credentials JSON file (e.g. ucs-ec2-tools.json)."""
    with open(path) as fd:
        data = json.load(fd)
    missing = [key for key in CREDENTIAL_KEYS if not data.get(key)]
    if missing:
        raise ValueError(f"{path}: missing/empty keys: {', '.join(missing)}")
    return data


class ProxmoxVNCBridge:
    """A TCP<->WebSocket bridge to a Proxmox VM's VNC console, run in a daemon thread."""

    def __init__(
        self,
        host: str,
        node: str,
        vmid: str,
        token_id: str,
        token_secret: str,
        port: int = 443,
        verify_tls: bool = False,
        bind_host: str = "127.0.0.1",
        bind_port: int = 0,
    ) -> None:
        if "://" in host:
            raise ValueError(f"proxmox_host must be a bare host name, not a URL: {host!r}")
        self.base_url = f"https://{host}:{port}"
        self.node = node
        self.vmid = vmid
        self.auth_header = {"Authorization": f"PVEAPIToken={token_id}={token_secret}"}
        self.bind_host = bind_host
        self.bind_port = bind_port

        self.ssl_ctx = ssl.create_default_context()
        if not verify_tls:  # Proxmox nodes usually present self-signed certs
            self.ssl_ctx.check_hostname = False
            self.ssl_ctx.verify_mode = ssl.CERT_NONE

        self._loop: asyncio.AbstractEventLoop | None = None
        self._server = None
        self._thread: threading.Thread | None = None
        self._ready = threading.Event()
        self._error: BaseException | None = None
        self._local_addr: tuple[str, int] | None = None
        self._vnc_port: int | None = None
        self._vnc_ticket: str | None = None

    @classmethod
    def from_credentials(
        cls, credentials: dict[str, str], node: str, vmid: str, port: int = 443, **kwargs,
    ) -> "ProxmoxVNCBridge":
        """Build a bridge from a parsed credentials dict (see :func:`load_credentials`)."""
        token_id = f"{credentials['proxmox_api_user']}!{credentials['proxmox_api_token_name']}"
        return cls(
            host=credentials["proxmox_host"],
            node=node,
            vmid=vmid,
            token_id=token_id,
            token_secret=credentials["proxmox_api_token_secret"],
            port=port,
            **kwargs,
        )

    def _get_vnc_ticket(self) -> tuple[int, str]:
        """POST /vncproxy to obtain the WebSocket port and the VNC ticket (= RFB password)."""
        url = f"{self.base_url}/api2/json/nodes/{quote(self.node, safe='')}/qemu/{quote(self.vmid, safe='')}/vncproxy"
        payload = urllib.parse.urlencode({"websocket": "1"}).encode()
        # base_url is a fixed https:// endpoint assembled from the config (see
        # __init__), so the scheme is not caller-controlled; S310 is a false positive.
        req = urllib.request.Request(url, data=payload, method="POST")  # noqa: S310
        req.add_header("Content-Type", "application/x-www-form-urlencoded")
        for key, value in self.auth_header.items():
            req.add_header(key, value)
        try:
            # base_url is a fixed https:// endpoint assembled from the config (see
            # __init__), so the scheme is not caller-controlled; S310 is a false positive.
            with urllib.request.urlopen(req, context=self.ssl_ctx) as resp:  # noqa: S310
                data = json.loads(resp.read())["data"]
        except urllib.error.HTTPError as exc:
            raise RuntimeError(f"Proxmox vncproxy request failed: POST {url}: HTTP {exc.code} {exc.reason}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"Proxmox vncproxy request failed: POST {url}: {exc.reason}") from exc
        return data["port"], data["ticket"]

    def start(self, timeout: float = 30.0) -> tuple[str, int, str]:
        """
        Fetch a VNC ticket, start the bridge thread and return (host, port, password).

        The returned password is the Proxmox VNC ticket; connect the VNC client to
        ``host::port`` with it right away, as the ticket is only valid briefly.
        """
        if websockets is None:
            raise RuntimeError("The 'websockets' package is required for the Proxmox VNC bridge")

        self._vnc_port, self._vnc_ticket = self._get_vnc_ticket()

        self._thread = threading.Thread(target=self._run, name="proxmox-vnc-bridge", daemon=True)
        self._thread.start()

        if not self._ready.wait(timeout):
            raise RuntimeError(f"Proxmox VNC bridge did not start within {timeout}s")
        if self._error:
            raise self._error

        assert self._local_addr is not None
        host, port = self._local_addr
        log.info("Proxmox VNC bridge listening on %s:%s (VM %s on node %s)", host, port, self.vmid, self.node)
        return host, port, self._vnc_ticket

    def _run(self) -> None:
        try:
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
            self._loop.run_until_complete(self._serve())
            self._loop.run_forever()
        except BaseException as exc:  # noqa: BLE001 - surface to start() via the event
            self._error = exc
            self._ready.set()

    async def _serve(self) -> None:
        self._server = await asyncio.start_server(self._handle_client, self.bind_host, self.bind_port)
        sock = self._server.sockets[0].getsockname()
        self._local_addr = (sock[0], sock[1])
        self._ready.set()

    async def _open_ws(self, ws_url: str):
        """
        Open the WebSocket, tolerating the header-kwarg rename across websockets releases.

        websockets >= 14 (asyncio client) uses ``additional_headers``; older/legacy
        releases use ``extra_headers``. Try the modern name, fall back to the old one.
        """
        common = {
            "ssl": self.ssl_ctx,
            "subprotocols": ["binary"],
            "max_size": None,
            "ping_interval": None,
        }
        try:
            return await websockets.connect(ws_url, additional_headers=self.auth_header, **common)
        except TypeError as exc:
            if "additional_headers" not in str(exc):
                raise
            return await websockets.connect(ws_url, extra_headers=self.auth_header, **common)

    async def _handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        peer = writer.get_extra_info("peername")
        log.debug("VNC client connected: %s", peer)
        try:
            qs = urllib.parse.urlencode({"port": self._vnc_port, "vncticket": self._vnc_ticket})
            host_port = self.base_url.replace("https://", "")
            ws_url = f"wss://{host_port}/api2/json/nodes/{quote(self.node, safe='')}/qemu/{quote(self.vmid, safe='')}/vncwebsocket?{qs}"

            ws = await self._open_ws(ws_url)
            try:
                await self._pump(reader, writer, ws)
            finally:
                await ws.close()
        except Exception as exc:  # noqa: BLE001 - a broken client must not kill the loop
            log.warning("Proxmox VNC bridge error: %s", exc)
        finally:
            writer.close()
            log.debug("VNC client disconnected: %s", peer)

    async def _pump(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter, ws) -> None:
        async def tcp_to_ws() -> None:
            while True:
                data = await reader.read(65536)
                if not data:
                    break
                await ws.send(data)

        async def ws_to_tcp() -> None:
            async for message in ws:
                if isinstance(message, str):
                    message = message.encode()
                writer.write(message)
                await writer.drain()

        _done, pending = await asyncio.wait(
            [asyncio.ensure_future(tcp_to_ws()), asyncio.ensure_future(ws_to_tcp())],
            return_when=asyncio.FIRST_COMPLETED,
        )
        for task in pending:
            task.cancel()
