"""Packet construction. All builders return complete frames ready for a raw socket."""
from __future__ import annotations

import ipaddress
import random
import socket
import struct


def checksum(data: bytes) -> int:
    if len(data) & 1:
        data += b"\x00"
    total = 0
    for i in range(0, len(data), 2):
        total += (data[i] << 8) | data[i + 1]
    total = (total >> 16) + (total & 0xFFFF)
    total += total >> 16
    return ~total & 0xFFFF


def rand_ip(net: ipaddress.IPv4Network | None = None) -> str:
    if net is None:
        return socket.inet_ntoa(struct.pack("!I", random.getrandbits(32)))
    return str(ipaddress.ip_address(int(net.network_address) + random.randrange(net.num_addresses)))


def rand_port() -> int:
    return random.randint(1024, 65535)


def build_ip(src: str, dst: str, proto: int, tot_len: int) -> bytes:
    def pack(c: int) -> bytes:
        return struct.pack(
            "!BBHHHBBH4s4s", 0x45, 0, tot_len, random.getrandbits(16), 0,
            random.choice((64, 128, 255)), proto, c,
            socket.inet_aton(src), socket.inet_aton(dst),
        )

    return pack(checksum(pack(0)))


def build_tcp(src: str, sport: int, dst: str, dport: int,
              seq: int, ack: int, flags: int, payload: bytes = b"") -> bytes:
    tlen = 20 + len(payload)

    def pack(c: int) -> bytes:
        return struct.pack("!HHIIBBHHH", sport, dport, seq, ack, 0x50, flags,
                           random.randint(1024, 65535), c, 0)

    pseudo = socket.inet_aton(src) + socket.inet_aton(dst) + struct.pack("!BBH", 0, 6, tlen)
    c = checksum(pseudo + pack(0) + payload)
    return build_ip(src, dst, socket.IPPROTO_TCP, 20 + tlen) + pack(c) + payload


def build_udp(src: str, sport: int, dst: str, dport: int, payload: bytes) -> bytes:
    ulen = 8 + len(payload)
    pseudo = socket.inet_aton(src) + socket.inet_aton(dst) + struct.pack("!BBH", 0, 17, ulen)
    hdr = struct.pack("!HHHH", sport, dport, ulen, 0)
    c = checksum(pseudo + hdr + payload)
    return (build_ip(src, dst, socket.IPPROTO_UDP, 20 + ulen)
            + struct.pack("!HHHH", sport, dport, ulen, c) + payload)


def dns_query(qname: str, qtype: int = 255, edns: int = 4096) -> bytes:
    """ANY query with an EDNS0 OPT record advertising a 4 KiB UDP buffer."""
    pkt = struct.pack("!HHHHHH", random.getrandbits(16), 0x0100, 1, 0, 0, 1)
    for label in qname.split("."):
        if label:
            pkt += bytes([len(label)]) + label.encode()
    pkt += b"\x00" + struct.pack("!HH", qtype, 1)
    pkt += b"\x00" + struct.pack("!HHIH", 41, edns, 0, 0)
    return pkt


# version 2, mode 7, implementation 3, request 42 (monlist)
NTP_MONLIST = b"\x17\x00\x03\x2a" + b"\x00" * 44

# LDAP rootDSE search, objectClass attribute, no base
CLDAP_ROOTDSE = (
    b"\x30\x25\x02\x01\x01\x63\x20\x04\x00\x0a\x01\x00\x0a\x01\x00"
    b"\x02\x01\x00\x02\x01\x00\x01\x01\x00\x87\x0b\x6f\x62\x6a\x65"
    b"\x63\x74\x63\x6c\x61\x73\x73\x30\x00"
)

SSDP_MSEARCH = (
    b"M-SEARCH * HTTP/1.1\r\nHOST: 239.255.255.250:1900\r\n"
    b'MAN: "ssdp:discover"\r\nMX: 1\r\nST: ssdp:all\r\n\r\n'
)
