# Scale

Honest numbers, one tuned gigabit VPS:

- ~1–2 Mpps of 60-byte frames
- ~120 MB/s of large frames
- ~15–30 k TLS requests/sec (Python)

That buries an unmitigated box and does nothing to Cloudflare. Anything fronted by a major CDN needs either 10+ nodes across providers or a rented stresser.

## Ceilings per vector

| vector | bottleneck |
|---|---|
| `syn`, `ack` | pps and NIC |
| `udp`, `psh` | bandwidth |
| `dns`, `ntp`, `memcached`, `cldap` | reflector quality, not you |
| `http` | TLS handshakes, CPU |
| `slowloris`, `rudy` | file descriptors and time |

## Python is the L7 ceiling

For request volume, run `h2load` or `wrk` alongside hydra rather than instead of it. Keep hydra for the raw and reflected layers where it has no real competition from Python tooling.

## When to stop building

If you need >10 Gbps sustained, buy the flood. If you need to understand or tune it, keep this.
