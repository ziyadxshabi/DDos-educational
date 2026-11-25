# Troubleshooting

**Counters rise, target sees nothing.** Upstream. Your spoof range is being dropped by uRPF or provider ACLs. Try `--spoof off`, try a range inside your provider's allocation, check with the provider.

**`PermissionError` on raw vectors.** Not root. `sudo`, or `setcap cap_net_raw+ep $(readlink -f $(which python3))`, or stick to L7.

**Throughput collapses after ~30s.** Conntrack table full. Confirm with `sysctl net.netfilter.nf_conntrack_count` against `_max`. `make tune` fixes it.

**`OSError: [Errno 105] No buffer space available`.** Send buffer too small, or the NIC queue is full. Run `make tune`, drop `--procs`, lower `-r`.

**DNS vector produces nothing.** Dead resolver list. Re-validate entries; public lists rot fast.

**NTP produces nothing.** Host has no mode 7. Test with `ntpdc -n -c monlist`.

**HTTP vector is slow.** Python. Raise `-t`, drop `--ssl` to isolate TLS cost, or use `h2load`.

**Slowloris dies at ~1000 connections.** `ulimit -n`. `make tune` sets 1048576.

**Nothing works on a cloud VM.** Some hypervisors filter spoofed frames. Try `--spoof off`; if that works, it is the hypervisor, and you need a provider that permits spoofing.
