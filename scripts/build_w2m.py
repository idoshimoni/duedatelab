"""
Weeks-to-months batch generator.

Phase 2 Step 5 (Option B), per round 1.5 research-AI consult.
Generates the full /pregnancy/weeks-to-months/N/ leaf set from the
deterministic w2m_data_schema records, rendered through w2m_leaf_template.

Modes:
  --staging       Write to dist/pregnancy/weeks-to-months-staging/N/ for
                  G2A sample review. Sitemap-excluded, robots-noindex
                  upstream until promotion.
  --production    Write to dist/pregnancy/weeks-to-months/N/ for live.
                  Only run after G2A sample gate has cleared.
  --weeks 1,3,23,27,42
                  Generate only listed weeks. Useful for the G2A sample.
                  Default is all 42.

Per round 1.5 must-fix list:
  - URL relationship frozen, leaves are self-canonical
  - Deterministic generation (this script + the schema is the single
    source of truth)
  - Edge-week handling (weeks 1-3 LMP note, weeks 41-42 no medical claims)
  - Unique title/H1/meta/canonical/breadcrumb per leaf

Usage:
    python3 scripts/build_w2m.py --staging
    python3 scripts/build_w2m.py --staging --weeks 1,3,23,27,42
    python3 scripts/build_w2m.py --production
"""

from __future__ import annotations
import argparse
import os
import sys

DIST = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from w2m_data_schema import build_all_records, make_record, MIN_WEEK, MAX_WEEK
from w2m_leaf_template import render_leaf


STAGING_DIR = os.path.join(DIST, "pregnancy", "weeks-to-months-staging")
PRODUCTION_DIR = os.path.join(DIST, "pregnancy", "weeks-to-months")


def _parse_weeks(weeks_arg: str | None) -> list[int]:
    if not weeks_arg:
        return list(range(MIN_WEEK, MAX_WEEK + 1))
    out = []
    for tok in weeks_arg.split(","):
        tok = tok.strip()
        if not tok:
            continue
        w = int(tok)
        if w < MIN_WEEK or w > MAX_WEEK:
            raise SystemExit(f"week {w} outside [{MIN_WEEK}, {MAX_WEEK}]")
        out.append(w)
    return out


def _write_leaf(record, base_dir: str, build_mode: str) -> str:
    """Write one leaf to base_dir/N/index.html. Returns the path."""
    week_dir = os.path.join(base_dir, str(record.week))
    os.makedirs(week_dir, exist_ok=True)
    path = os.path.join(week_dir, "index.html")
    html = render_leaf(record, build_mode=build_mode)
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    return path


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--staging", action="store_true",
                      help="write to weeks-to-months-staging/")
    mode.add_argument("--production", action="store_true",
                      help="write to weeks-to-months/ (live URL family)")
    ap.add_argument("--weeks", default=None,
                    help="comma-separated week numbers, e.g. 1,3,23,27,42. "
                         "Default is all 42.")
    args = ap.parse_args()

    base = STAGING_DIR if args.staging else PRODUCTION_DIR
    os.makedirs(base, exist_ok=True)
    weeks = _parse_weeks(args.weeks)
    build_mode = "staging" if args.staging else "production"

    written = []
    for w in weeks:
        rec = make_record(w)
        path = _write_leaf(rec, base, build_mode)
        rel = os.path.relpath(path, DIST)
        written.append(rel)

    label = "STAGING" if args.staging else "PRODUCTION"
    print(f"[{label}] wrote {len(written)} leaves to {os.path.relpath(base, DIST)}/")
    for r in written:
        print(f"  {r}")


if __name__ == "__main__":
    main()
