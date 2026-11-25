# Contributing

## Adding a vector

1. Put it in `hydra/vectors/l4.py` or `l7.py`.
2. Register it in that module's `VECTORS` dict.
3. Add a row to `docs/01-vectors.md` with layer, spoofing, and when to use it.
4. If it needs a reflector list, add a file under `hydra/data/` and a `--flag` in `cli.py`.
5. Add a builder test if it constructs packets.

## Rules

- Stdlib only. No runtime dependencies.
- One function per vector, signature `(Ctx) -> None`.
- Never raise on a per-packet failure; `runtime.worker` swallows, but keep it clean.
- Spoof through `rand_ip(ctx.net)`, never a hardcoded IP.
- `ruff check` and `python -m unittest discover -s tests` must pass.

## Style

Line length 100, type hints on public functions, no docstring theatre.
