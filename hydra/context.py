"""Per-process shared context and reflector list loading."""
from __future__ import annotations

import ipaddress
import socket
from pathlib import Path

_DATA = Path(__file__).parent / "data"


def _local_ip(dst: str) -> str:
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        try:
            s.connect((dst, 80))
            return s.getsockname()[0]
        except OSError:
            return "127.0.0.1"


def load_list(path: str | None, default: str) -> list[str]:
    """Load a reflector list from a file, or fall back to a packaged default."""
    target = Path(path) if path else (_DATA / default)
    return [
        line.strip()
        for line in target.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    ]


class Ctx:
    """Immutable-ish parameters plus lazily created raw sockets."""

    __slots__ = ("dst", "dport", "target_host", "net", "src_ip", "domain",
                 "resolvers", "ntp", "memcached", "ssdp", "cldap", "uas",
                 "ssl", "path", "method", "junk", "keepalive", "sock", "udp_sock")

    def __init__(self, args, dst: str):
        self.dst = dst
        self.dport = args.port
        self.target_host = args.host
        self.src_ip = _local_ip(dst) if args.spoof == "off" else None
        self.net = (ipaddress.ip_network(args.spoof)
                    if args.spoof not in ("off", "auto") else None)
        self.domain = args.domain or args.host
        self.resolvers = load_list(args.resolvers, "resolvers.txt")
        self.ntp = load_list(args.ntp, "ntp.txt")
        self.memcached = load_list(args.memcached, "memcached.txt")
        self.ssdp = load_list(args.ssdp, "ssdp.txt")
        self.cldap = load_list(args.cldap, "cldap.txt")
        self.uas = load_list(args.ua, "uas.txt")
        self.ssl = args.ssl
        self.path = args.path
        self.method = args.http_method
        self.junk = args.junk
        self.keepalive = args.keepalive
        self.sock = None
        self.udp_sock = None

    def raw(self) -> socket.socket:
        if self.sock is None:
            s = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_RAW)
            s.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)
            for opt, val in ((socket.SO_SNDBUF, 4 << 20), (socket.SO_RCVBUF, 4 << 20)):
                try:
                    s.setsockopt(socket.SOL_SOCKET, opt, val)
                except OSError:
                    pass
            self.sock = s
        return self.sock

    def udp_raw(self) -> socket.socket:
        if self.udp_sock is None:
            s = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_RAW)
            s.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)
            self.udp_sock = s
        return self.udp_sock