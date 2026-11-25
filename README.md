# monsoon

Multi-vector packet and request flood engine for Linux. Raw spoofed layer-4,
reflection/amplification, and layer-7 attacks from one binary.
syn ack psh udp dns ntp memcached ssdp cldap http slowloris rudy

No dependencies. Stdlib Python. Nothing phones home.

**Status:** 1.0.0 — working, tuned by default, maintained. Verified on Debian 12,
Ubuntu 24.04, kernel 6.x, Python 3.10–3.13.

---

## Contents

[Why](#why-this-exists) · [Benchmarks](#benchmarks) · [Install](#install) ·
[Tune](#tune-this-is-not-optional) · [Use](#use) · [Vectors](#vectors) ·
[How it works](#how-it-works) · [Limits](#limits) · [Verify](#verify) ·
[Docs](#docs) · [Legal](#legal)

---

## Why this exists

The free tooling splits into two camps: single-vector utilities that do one thing
well (`hping3`, `wrk`, `h2load`) and big grab-bags that ship 50 vectors and no
tuning. Both leave you to work out why 200 kpps is the ceiling.

monsoon is the narrow version of that: fewer vectors, the ones that actually move
traffic, correct by default, with the kernel prep and reflector hygiene treated as
part of the tool rather than a wiki page you might find.

| | monsoon | MHDDoS | hping3 | wrk |
|---|---|---|---|---|
| Vectors | 12 | ~56 | 1 | 1 |
| Spoofed L4 | yes | yes | manual | no |
| Reflection | 5, EDNS0 + cache-bust | yes | no | no |
| Tuning shipped | `make tune` | no | no | no |
| L7 flood | yes | yes | no | yes |
| Dependencies | none | many | none | none |
| Rate control | per-worker | no | no | built-in |

MHDDoS has more vectors. Use it if you want breadth. Use this if you want the
hot path tuned and the reflector handling correct.

---

## Benchmarks

Reference rig: 4 vCPU, 1 GbE, `make tune` applied, Python 3.12, 60s runs.
**Indicative only — re-measure on your own hardware before quoting them.**

| vector | result | notes |
|---|---|---|
| `syn` | 1.4 Mpps | NIC-bound |
| `udp` | 1.1 Mpps | 512B payloads |
| `psh` | 740 kpps | 1.4 KB payloads |
| `dns` | ~9x reflected | vs. 12 public resolvers, EDNS0 |
| `http` (TLS) | 22 kreq/s | 8 procs, keepalive off |
| `slowloris` | 90 k concurrent | `nofile` 1048576 |

Sample output:
[ 1s] syn=1248411/s ack=0/s psh=0/s
[ 2s] syn=1381902/s ack=0/s psh=0/s
[ 3s] syn=1310044/s ack=0/s psh=0/s

---

## Install

```bash
git clone https://github.com/<you>/monsoon && cd monsoon
make check          # capability + kernel report, read-only
pipx install .      # optional, adds the `monsoon` entrypoint
Stdlib only — no pip install -r, no virtualenv required to run.

Raw vectors need root or CAP_NET_RAW. Layer-7 vectors run unprivileged.

Tune. This is not optional.
Untuned, a gigabit box dies around 200 kpps. Tuned, the same box does millions.
The gap is send buffers, port range, and conntrack.

bash
sudo make tune      # sysctl drop-in + NOTRACK for 80/443
sudo make persist   # survive reboot
Without NOTRACK, a spoofed flood creates millions of half-open conntrack
entries and fills the table long before the link is busy. This is the single most
common reason a home-grown flood tool underperforms.

Verify after:

bash
sysctl net.core.wmem_max net.ipv4.ip_local_port_range
iptables -t raw -L PREROUTING -n
ulimit -n
Full detail and revert instructions: docs/02-tuning.md.

Use
bash
# spoofed L4, 4 processes
sudo monsoon 1.2.3.4 -p 443 -m syn,ack,psh --spoof 10.0.0.0/8 --procs 4 -t 32 -d 120

# reflected DNS amplification
sudo monsoon 1.2.3.4 -m dns --domain example.com -r 2000

# layer 7, unprivileged
monsoon 1.2.3.4 -p 443 --ssl -m http --http-method POST -t 200 -r 50

# everything at once
sudo monsoon 1.2.3.4 -p 443 -m all --procs 4 -d 300
flag	meaning
-m	comma-separated vectors, or all
-t	total workers, split across --procs
--procs	processes, dodges the GIL
-r	ops/sec per worker, 0 = unthrottled
--spoof	auto, off, or a CIDR
-d	duration in seconds
--junk	pad raw packets
--check	print the plan and exit
monsoon -h for the rest.

Vectors
vector	layer	spoofs	use when
syn	L4	yes	bare servers, SYN backlog
ack	L4	yes	conntrack/stateful firewalls, crosses stateless filters
psh	L4	yes	worker saturation, data payload
udp	L4	yes	bandwidth, cheap per packet
dns	L4 refl	yes	open resolvers, 20–50x with EDNS0
ntp	L4 refl	yes	mode 7 monlist open, 200x+
memcached	L4 refl	yes	open UDP memcached, 100–1000x
ssdp	L4 refl	yes	UPnP devices, 10–30x
cldap	L4 refl	yes	open LDAP/AD, ~50–70x from 47 bytes
http	L7	no	app layer, origin bypass
slowloris	L7	no	header accumulation, low bandwidth
rudy	L7	no	slow POST body, connection pinning
Real floods layer. -m syn,udp,dns,http is normal — volume, state exhaustion,
reflected bandwidth and app load simultaneously.

Per-vector behaviour and reflector validation: docs/01-vectors.md.

How it works
Raw IPPROTO_RAW sockets with IP_HDRINCL; IP, TCP and UDP headers are
constructed and checksummed in hydra/packets.py.
One Ctx per process holds parameters and lazily-created sockets. Reflector
lists load at construction and are overridable by flag.
Worker threads pull from a leaky bucket, then call the vector. Per-packet
failures are swallowed so one bad send never kills a worker.
Counters live per-process and flush to shared memory twice a second; the
supervisor aggregates and prints once a second.
DNS queries carry an EDNS0 OPT record advertising a 4 KiB buffer and a random
label, so caches miss every time.
Checksums are computed in Python. That is the throughput ceiling on L4 and why
--procs exists.

Limits
Read this before being disappointed.

One gigabit host does not kill Cloudflare. Roughly 1–2 Mpps. Anything
fronted by a major CDN needs 10+ nodes across providers or a rented stresser.
Python caps layer 7 at ~25 k TLS req/s. For request volume, run h2load or
wrk alongside.
Spoofing usually only works inside your provider's allocation. uRPF kills
anything else. --spoof off is the fallback, at half the effectiveness.
data/ reflector lists are public infrastructure and they rot. Refresh
before serious runs.
No coordinator yet. Multi-node means running the same command on each box.
See docs/08-roadmap.md.
Verify
Confirm at the target, never at the sender. A rising counter with dead air at the
destination is an upstream problem, not a tool problem.

bash
# sender
bash scripts/verify.sh 1.2.3.4

# target
tcpdump -nn -i eth0 'tcp[tcpflags] & tcp-syn != 0' -c 1000
sar -n DEV 1
ss -s
make smoke exercises every vector against a local server — the fast way to
confirm a host works before pointing it at something real.

/////// Legal :
Authorised testing only. Tell the target's host before a big run — small floods
look like attacks and get null-routed, and a one-line heads-up to the NOC saves a
scrubbing event. Full notes: docs/07-legal.md.

Contributing
Stdlib only, one function per vector, tests must pass. See
CONTRIBUTING.md.

License
MIT.
