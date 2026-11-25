# Vectors

Reference table of the 12 vectors in `hydra/vectors/l4.py` and `hydra/vectors/l7.py`.

| Vector | Layer | Port | Spoofing | Mechanism |
| :--- | :--- | :--- | :--- | :--- |
| `syn` | L4 | configurable | Yes | TCP `SYN` frames with random source ports and optional `--junk` payload |
| `ack` | L4 | configurable | Yes | Unsolicited TCP `ACK` frames with random sequence/ack numbers |
| `psh` | L4 | configurable | Yes | TCP `PSH+ACK` frames carrying 200–1400 bytes of random payload |
| `udp` | L4 | configurable | Yes | Raw UDP datagrams with 16–1024 bytes of random payload |
| `dns` | L4 refl | UDP/53 | Yes | `ANY` queries with EDNS0 4096-byte buffer and random subdomain labels |
| `ntp` | L4 refl | UDP/123 | Yes | 48-byte NTPv2 mode-7 `monlist` request frames |
| `memcached` | L4 refl | UDP/11211 | Yes | UDP `stats items\r\n` command frames |
| `ssdp` | L4 refl | UDP/1900 | Yes | UPnP `M-SEARCH` discovery requests (`ST: ssdp:all`) |
| `cldap` | L4 refl | UDP/389 | Yes | BER-encoded CLDAP `rootDSE` search requests |
| `http` | L7 | TCP/HTTP(S) | No | TCP/TLS sockets sending cache-busted `GET` or `POST` requests |
| `slowloris` | L7 | TCP/HTTP | No | Trickles partial HTTP headers every 0.8s to hold worker slots |
| `rudy` | L7 | TCP/HTTP | No | Sends `Content-Length: 1000000` POST headers and trickles 1 byte every 0.7s |