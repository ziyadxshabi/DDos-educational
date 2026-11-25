# Roadmap

Planned, not built.

- [ ] **Coordinator** — one control host, N agents over a socket, synchronised start/stop, per-node spoof-range assignment and aggregate stats.
- [ ] **Adaptive mode** — poll the target, measure response latency and status codes, rotate vectors and raise rate on degradation.
- [ ] **Reflector scanner** — sweep a CIDR for open DNS/NTP/memcached/CLDAP and emit a validated list, replacing the static `data/` files.
- [ ] **L7 over asyncio** — single-threaded event loop per process for higher request rates than threads allow.
- [ ] **`--dry-run` packet dump** — hexdump of the first N frames per vector for offline inspection.
- [ ] **pcap export** — write a sample of generated traffic for Wireshark.
