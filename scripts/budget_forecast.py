"""Forecast whether the remaining Claude Code usage covers the next WRK-TASK.

Reads local Claude Code transcripts (``~/.claude/projects/**/*.jsonl``), never sends
anything anywhere. It derives a per-session token baseline for this project and the
rolling consumption of the current 5-hour window, then prints KPIs and a GO / CAUTION
/ STOP verdict for starting one more task.

The real weekly/5h plan allowance is not machine-readable. Fastest path: run
``/status`` and pass what it shows, e.g. ``--session-pct 37 --weekly-pct 4
--reset-min 48``; the script back-calculates the ceilings from the usage it already
measured. Alternatively set them once in ``.claude/budget.local.json``
(``{"blockCeiling": 1500000, "weeklyCeiling": 15000000}``). Without either, it falls
back to the largest historical 5-hour window as a proxy and lowers confidence.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
from dataclasses import dataclass
from pathlib import Path

BLOCK = dt.timedelta(hours=5)
WEEK = dt.timedelta(days=7)

# Weights approximating how each token class counts toward Anthropic usage limits.
# Cache reads are billed and rate-limited at a fraction of fresh input; overridable
# via .claude/budget.local.json ("weights": {...}).
DEFAULT_WEIGHTS = {
    "input_tokens": 1.0,
    "cache_creation_input_tokens": 1.0,
    "cache_read_input_tokens": 0.1,
    "output_tokens": 1.0,
}


@dataclass
class Session:
    path: Path
    cwd: str | None
    start: dt.datetime
    end: dt.datetime
    tokens: int


def _tokens(usage: dict, weights: dict[str, float]) -> int:
    """Weighted billable tokens for one assistant message."""
    return round(sum(weights[key] * int(usage.get(key, 0)) for key in weights))


def _norm(path: str | None) -> str:
    return str(path).strip().rstrip("/\\").casefold() if path else ""


def _parse(path: Path, weights: dict[str, float]) -> Session | None:
    start: dt.datetime | None = None
    end: dt.datetime | None = None
    cwd: str | None = None
    total = 0
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        cwd = cwd or row.get("cwd")
        stamp = row.get("timestamp")
        if stamp:
            moment = dt.datetime.fromisoformat(stamp.replace("Z", "+00:00"))
            start = moment if start is None else min(start, moment)
            end = moment if end is None else max(end, moment)
        usage = (row.get("message") or {}).get("usage")
        if usage:
            total += _tokens(usage, weights)
    if start is None or end is None or total == 0:
        return None
    return Session(path=path, cwd=cwd, start=start, end=end, tokens=total)


def _load(
    projects_dir: Path, project_path: Path, weights: dict[str, float]
) -> tuple[list[Session], list[Session]]:
    target = _norm(str(project_path))
    everything: list[Session] = []
    mine: list[Session] = []
    for jsonl in projects_dir.glob("*/*.jsonl"):
        session = _parse(jsonl, weights)
        if session is None:
            continue
        everything.append(session)
        if _norm(session.cwd) == target:
            mine.append(session)
    return everything, mine


def _percentile(values: list[int], fraction: float) -> int:
    if not values:
        return 0
    ordered = sorted(values)
    index = min(len(ordered) - 1, round(fraction * (len(ordered) - 1)))
    return ordered[index]


def _rolling_block(sessions: list[Session], now: dt.datetime) -> int:
    cutoff = now - BLOCK
    return sum(s.tokens for s in sessions if s.end >= cutoff)


def _largest_block(sessions: list[Session]) -> int:
    best = 0
    for anchor in sorted(s.start for s in sessions):
        window = sum(s.tokens for s in sessions if anchor <= s.start < anchor + BLOCK)
        best = max(best, window)
    return best


def _fmt(value: int) -> str:
    return f"{value:,}"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--projects-dir",
        type=Path,
        default=Path.home() / ".claude" / "projects",
        help="Claude Code transcripts directory.",
    )
    parser.add_argument(
        "--project-path",
        type=Path,
        default=Path.cwd(),
        help="Repo path to match against each transcript's cwd.",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path(".claude/budget.local.json"),
        help="Optional ceilings file.",
    )
    parser.add_argument(
        "--task-cost",
        type=int,
        default=0,
        help="Override the estimated cost of the next task, in tokens.",
    )
    parser.add_argument(
        "--session-pct",
        type=float,
        default=0.0,
        help="Percent of the 5h session used, from /status. Calibrates blockCeiling.",
    )
    parser.add_argument(
        "--weekly-pct",
        type=float,
        default=0.0,
        help="Percent of the weekly allowance used, from /status. Calibrates weeklyCeiling.",
    )
    parser.add_argument(
        "--reset-min",
        type=int,
        default=0,
        help="Minutes until the 5h session resets, from /status.",
    )
    args = parser.parse_args()

    if not args.projects_dir.is_dir():
        parser.error(f"No transcripts directory at {args.projects_dir}")

    config: dict = {}
    if args.config.is_file():
        config = json.loads(args.config.read_text(encoding="utf-8"))

    weights = {**DEFAULT_WEIGHTS, **config.get("weights", {})}

    now = dt.datetime.now(dt.UTC)
    everything, mine = _load(args.projects_dir, args.project_path, weights)

    # Drop the still-open session (this one) so it does not skew the baseline.
    closed = [s for s in mine if s.end < now - dt.timedelta(minutes=3)]
    baseline = [s.tokens for s in sorted(closed, key=lambda s: s.end)[-10:]]

    task_p50 = _percentile(baseline, 0.5)
    task_p80 = _percentile(baseline, 0.8)
    confidence = "alta" if len(baseline) >= 5 else "media" if len(baseline) >= 3 else "baja"
    # With a thin baseline the p80 is dominated by a single outlier; use the median.
    estimate = task_p80 if len(baseline) >= 5 else task_p50
    task_cost = args.task_cost or estimate

    block_used = _rolling_block(everything, now)
    week_used = sum(s.tokens for s in everything if s.end >= now - WEEK)

    # A single /status percentage back-calculates the ceiling from measured usage:
    # ceiling = used / (pct / 100). Other devices inflate the real pct, so a
    # transcript-only "used" yields a conservative (smaller) ceiling. Good enough.
    block_ceiling = int(config.get("blockCeiling") or 0)
    weekly_ceiling = int(config.get("weeklyCeiling") or 0)
    calibrated = False
    if args.session_pct > 0 and block_used > 0:
        block_ceiling = round(block_used / (args.session_pct / 100))
        calibrated = True
    if args.weekly_pct > 0 and week_used > 0:
        weekly_ceiling = round(week_used / (args.weekly_pct / 100))
        calibrated = True

    proxy = block_ceiling <= 0
    if proxy:
        block_ceiling = _largest_block(everything)
    block_left = max(0, block_ceiling - block_used)

    burn = sum(s.tokens for s in everything if s.end >= now - dt.timedelta(hours=1))

    week_left = max(0, weekly_ceiling - week_used) if weekly_ceiling else 0

    headroom = (block_left / task_cost) if task_cost else float("inf")
    weekly_blocks = weekly_ceiling and task_cost and week_left < task_cost
    if task_cost == 0:
        verdict = "SIN DATOS — ejecuta 1-2 WRK-TASK para construir baseline"
    elif weekly_blocks:
        verdict = "STOP — el límite semanal no cubre otra tarea"
    elif proxy:
        verdict = (
            "SIN TECHO FIABLE — pásame los datos de /status con "
            "--session-pct N --weekly-pct M (o pon blockCeiling en "
            ".claude/budget.local.json); los KPIs de arriba son orientativos"
        )
    elif headroom >= 2.0:
        verdict = "GO — margen para la siguiente tarea"
    elif headroom >= 1.2:
        verdict = "CAUTION — cabe una tarea, revisa antes de la siguiente"
    else:
        verdict = "STOP — no empieces otra tarea en este bloque"

    # A block-only STOP/CAUTION is moot if the 5h window resets imminently.
    if (
        args.reset_min
        and 0 < args.reset_min <= 60
        and not weekly_blocks
        and verdict.startswith(("STOP", "CAUTION"))
    ):
        verdict += f"  ·  o espera {args.reset_min} min al reset del bloque"

    used_pct = f"  ({block_used / block_ceiling:.0%})" if block_ceiling else ""
    if proxy:
        proxy_note = "  (proxy: mayor bloque histórico)"
    elif calibrated:
        proxy_note = "  (calibrado con /status)"
    else:
        proxy_note = ""
    print("== Previsión de presupuesto (Claude Code) ==")
    print(f"Sesiones del proyecto analizadas : {len(mine)} (baseline: {len(baseline)})")
    print(f"Confianza del pronóstico         : {confidence}")
    print()
    print("KPIs")
    label = "p80" if len(baseline) >= 5 else "mediana"
    print(f"  Coste por tarea p50 / p80       : {_fmt(task_p50)} / {_fmt(task_p80)} tok")
    print(f"  Coste estimado próxima tarea ({label}): {_fmt(task_cost)} tok")
    print(f"  Techo por bloque de 5 h         : {_fmt(block_ceiling)} tok{proxy_note}")
    print(f"  Consumido en el bloque actual   : {_fmt(block_used)} tok{used_pct}")
    print(f"  Presupuesto restante en bloque  : {_fmt(block_left)} tok")
    if weekly_ceiling:
        print(f"  Semana: usado / restante        : {_fmt(week_used)} / {_fmt(week_left)} tok")
    if args.reset_min:
        print(f"  Reset del bloque en             : {args.reset_min} min")
    print(f"  Ritmo última hora               : {_fmt(burn)} tok/h")
    print(f"  Holgura (restante / coste tarea): {headroom:.1f}x")
    print()
    print(f"Veredicto: {verdict}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
