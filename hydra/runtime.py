"""Worker scheduling, rate control and shared counters."""
from __future__ import annotations

import threading
import time

from .context import Ctx
from .vectors import VECTORS


class Bucket:
    """Leaky bucket. A rate of 0 means unthrottled."""

    __slots__ = ("rate", "next")

    def __init__(self, rate: float):
        self.rate = rate
        self.next = time.perf_counter()

    def acquire(self) -> bool:
        if not self.rate:
            return True
        now = time.perf_counter()
        if now < self.next:
            return False
        self.next = now + 1.0 / self.rate
        return True


class Counter:
    __slots__ = ("n",)

    def __init__(self):
        self.n = 0


def worker(fn, ctx: Ctx, counter: Counter, bucket: Bucket, stop) -> None:
    while not stop.is_set():
        if not bucket.acquire():
            continue
        try:
            fn(ctx)
            counter.n += 1
        except Exception:
            pass


def flusher(local: list[Counter], shared, base: int, stop) -> None:
    """Publish per-process counters to shared memory twice a second."""
    while not stop.is_set():
        time.sleep(0.5)
        for i, cnt in enumerate(local):
            shared[base + i] = cnt.n


def proc_main(args, dst: str, selected: list[str], shared, slot: int, stop, procs: int) -> None:
    base = slot * len(selected)
    local = [Counter() for _ in selected]
    ctx = Ctx(args, dst)

    threading.Thread(target=flusher, args=(local, shared, base, stop), daemon=True).start()

    per = max(1, args.threads // procs) if args.threads else 8
    threads = []
    for i, name in enumerate(selected):
        for _ in range(per):
            t = threading.Thread(
                target=worker,
                args=(VECTORS[name], ctx, local[i], Bucket(args.rate), stop),
                daemon=True,
            )
            t.start()
            threads.append(t)
    for t in threads:
        t.join()
