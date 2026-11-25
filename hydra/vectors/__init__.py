"""Vector registry."""
from __future__ import annotations

from collections.abc import Callable

from . import l4, l7

VECTORS: dict[str, Callable] = {**l4.VECTORS, **l7.VECTORS}
RAW: frozenset[str] = frozenset(l4.VECTORS)
L7: frozenset[str] = frozenset(l7.VECTORS)