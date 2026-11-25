# Contributing

## Adding a vector

1. Add the function in `hydra/vectors/l4.py` or `hydra/vectors/l7.py`.
2. Register it in that module's `VECTORS` dict.
3. Add a row to `docs/01-vectors.md` with layer, spoofing, and lab use case.
4. If it uses a reflector list, add a file under `hydra/data/` and a `--flag` in `hydra/cli.py`.

## Rules

- Stdlib only. No third-party runtime dependencies.
- One function per vector, signature `(Ctx) -> None`.
- Spoof through `rand_ip(ctx.net)`, never a hardcoded IP.
- `ruff check hydra` and `python -m hydra --help` must pass.