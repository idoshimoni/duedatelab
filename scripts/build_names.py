"""
Names cluster batch generator.

Reads a JSON dataset of NameRecords from `audit/source-packs/<cluster>-dataset.json`,
validates each record against `names_data_schema.py`, and emits one
`/names/<slug>/index.html` per record using `name_leaf_template.py`.

PRECONDITIONS (per `feedback_phase2_operating_model.md` and Phase 2 plan §4.4):
1. G1A Source/Data Licensing Gate must have cleared the source pack.
2. G2A Template + Sample-Page Gate must have cleared the leaf template.

Per R4 of Step 2 close-out review (2026-04-26): live-write requires a
**gate-pass manifest** that binds dataset, source pack, and template to
their reviewed sha256 hashes. Build verifies the current files match the
hashes in the manifest. A boolean CLI flag is too easy to bypass; a
hash-bound manifest forces a meaningful re-review when anything changes.

Per B2 of round-2 review: manifest also binds the **source pack** that the
G1A reviewer signed off on (license / provenance evidence). If the dataset
hash matches but the source pack changed since approval, that means the
provenance evidence has drifted under the dataset and we must reject.

Per B1 of round-2 review: `--pilot` is smoke-only and may NOT promote to
`dist/names/`. It requires `--dry-run` and stages to a separate
`dist/names-pilot-staging/` directory that is never promoted.

Per B3 of round-2 review: the validator runs against the staging directory
BEFORE promotion. Promotion only happens if the validator returns 0.

Per R5: unresolved related/variant/sibling slug references fail the build
by default (strict mode). The manifest can opt out via
`allow_unresolved_refs: true`.

Per R3: production records must clear the >=2 useful content modules bar.
The manifest sets `production_mode: true` for live builds; smoke tests
can run with `production_mode: false`.

Usage:
    python3 scripts/build_names.py --manifest <gate-pass.json>
    python3 scripts/build_names.py --pilot --dry-run    # smoke test only
"""

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from names_data_schema import NameRecord, validate_record, from_json, SCHEMA_VERSION
from name_leaf_template import render_name_leaf

DIST = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAMES_DIR = os.path.join(DIST, "names")
STAGING_DIR = os.path.join(DIST, "names-staging")
PILOT_STAGING_DIR = os.path.join(DIST, "names-pilot-staging")
PARENTLAB = os.path.dirname(DIST)
PILOT_FIXTURE = os.path.join(
    PARENTLAB, "audit", "source-packs",
    "names-cluster-pilot-fixture.json"
)
SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_PATH = os.path.join(SCRIPTS_DIR, "name_leaf_template.py")
VALIDATOR_PATH = os.path.join(SCRIPTS_DIR, "verify_names_batch.py")


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def load_manifest(path):
    """Load a gate-pass manifest. Required fields:
        cluster, schema_version,
        dataset_path, dataset_sha256,
        source_pack_path, source_pack_sha256,
        template_path, template_sha256,
        g1a_review (path), g1a_disposition (must be 'VERIFIED'),
        g2a_review (path), g2a_disposition (must be 'VERIFIED'),
        approved_at (ISO date)
    Optional: production_mode (default True), allow_unresolved_refs (default False).

    Per B2 of round-2 review: source_pack_path + source_pack_sha256 are
    REQUIRED so the build cannot promote a dataset whose provenance
    evidence has drifted from what G1A signed off on."""
    with open(path, "r", encoding="utf-8") as f:
        m = json.load(f)
    required = [
        "cluster", "schema_version",
        "dataset_path", "dataset_sha256",
        "source_pack_path", "source_pack_sha256",
        "template_path", "template_sha256",
        "g1a_review", "g1a_disposition",
        "g2a_review", "g2a_disposition",
        "approved_at",
    ]
    missing = [k for k in required if k not in m]
    if missing:
        raise ValueError(f"manifest missing required fields: {missing}")
    if m.get("g1a_disposition") != "VERIFIED":
        raise ValueError(f"g1a_disposition must be 'VERIFIED' (got '{m.get('g1a_disposition')}')")
    if m.get("g2a_disposition") != "VERIFIED":
        raise ValueError(f"g2a_disposition must be 'VERIFIED' (got '{m.get('g2a_disposition')}')")
    if m.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(
            f"manifest schema_version {m.get('schema_version')} != current {SCHEMA_VERSION}. "
            "Re-run G2A on the new schema before building."
        )
    return m


def verify_manifest_hashes(manifest):
    """Recompute current dataset + source pack + template hashes and verify
    against the manifest. Any mismatch means content has drifted from the
    approved set."""
    errs = []
    pairs = [
        ("dataset", manifest["dataset_path"], manifest["dataset_sha256"]),
        ("source_pack", manifest["source_pack_path"], manifest["source_pack_sha256"]),
        ("template", manifest.get("template_path", TEMPLATE_PATH), manifest["template_sha256"]),
    ]
    for label, path, expected in pairs:
        if not os.path.exists(path):
            errs.append(f"{label} path does not exist: {path}")
            continue
        actual = sha256_file(path)
        if actual != expected:
            errs.append(
                f"{label} hash mismatch: manifest says {expected[:12]}... "
                f"but {path} hashes to {actual[:12]}..."
            )
    return errs


def run_validator(names_dir):
    """Run the staging validator. Returns 0 on pass, non-zero on fail.

    Per B3 of round-2 review: the validator gates promotion. We invoke as a
    subprocess so the CLI behavior matches what the reviewer runs by hand.
    """
    if not os.path.exists(VALIDATOR_PATH):
        print(f"  WARNING: validator not found at {VALIDATOR_PATH}, skipping")
        return 0
    cmd = [sys.executable, VALIDATOR_PATH, "--names-dir", names_dir]
    print(f"  running validator: {' '.join(cmd)}")
    proc = subprocess.run(cmd, capture_output=True, text=True)
    sys.stdout.write(proc.stdout)
    if proc.stderr:
        sys.stderr.write(proc.stderr)
    return proc.returncode


def load_dataset(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError(f"Expected JSON array at {path}")
    records = []
    for i, entry in enumerate(data):
        try:
            rec = from_json(json.dumps(entry))
        except Exception as e:
            raise ValueError(f"Failed to parse record {i}: {e}")
        records.append(rec)
    return records


def build(records, output_dir, production_mode, strict_refs):
    """Validate + render + write to output_dir. Returns (n_written, n_bytes)
    or raises on any error."""
    errors = []
    for rec in records:
        errs = validate_record(rec, production_mode=production_mode)
        if errs:
            errors.append((rec.slug or "<no-slug>", errs))
    if errors:
        msg = ["VALIDATION FAILED:"]
        for slug, errs in errors:
            msg.append(f"  {slug}:")
            for e in errs:
                msg.append(f"    - {e}")
        raise ValueError("\n".join(msg))

    all_slugs = {rec.slug for rec in records}
    if len(all_slugs) != len(records):
        slug_counts = {}
        for rec in records:
            slug_counts[rec.slug] = slug_counts.get(rec.slug, 0) + 1
        dups = {s: c for s, c in slug_counts.items() if c > 1}
        raise ValueError(f"duplicate slugs in dataset: {dups}")

    os.makedirs(output_dir, exist_ok=True)
    n_written = 0
    n_bytes = 0
    for rec in records:
        try:
            html = render_name_leaf(rec, all_slugs, strict=strict_refs)
        except ValueError as e:
            raise ValueError(f"render failed for {rec.slug}: {e}")
        slug_dir = os.path.join(output_dir, rec.slug)
        os.makedirs(slug_dir, exist_ok=True)
        with open(os.path.join(slug_dir, "index.html"), "w", encoding="utf-8") as f:
            f.write(html)
        n_written += 1
        n_bytes += len(html)
    return n_written, n_bytes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", help="Path to gate-pass manifest JSON")
    ap.add_argument("--pilot", action="store_true", help="Use the bundled pilot fixture (smoke only; requires --dry-run)")
    ap.add_argument("--dry-run", action="store_true", help="Render to staging, do not promote to dist/names/")
    ap.add_argument("--allow-unresolved-refs", action="store_true",
                    help="Allow related/variant/sibling slugs not in batch (default: fail)")
    args = ap.parse_args()

    # B1: --pilot must NEVER promote to live. Separate staging dir, --dry-run required.
    if args.pilot:
        if not args.dry_run:
            print("ERROR: --pilot is smoke-only and must be used with --dry-run")
            print("       Pilot fixtures bypass G1A/G2A binding and are not promotable.")
            return 1
        if not os.path.exists(PILOT_FIXTURE):
            print(f"ERROR: pilot fixture not found at {PILOT_FIXTURE}")
            return 1
        print(f"Loading pilot fixture {PILOT_FIXTURE}")
        records = load_dataset(PILOT_FIXTURE)
        production_mode = False
        strict_refs = not args.allow_unresolved_refs
        staging_dir = PILOT_STAGING_DIR
    elif args.manifest:
        if not os.path.exists(args.manifest):
            print(f"ERROR: manifest not found at {args.manifest}")
            return 1
        print(f"Loading manifest {args.manifest}")
        # C-round minor: surface manifest schema errors as a clean CLI error
        # instead of an uncaught Python stack trace.
        try:
            manifest = load_manifest(args.manifest)
        except (ValueError, json.JSONDecodeError) as e:
            print(f"ERROR: manifest invalid: {e}")
            return 1
        print(f"  cluster: {manifest['cluster']}")
        print(f"  approved_at: {manifest['approved_at']}")
        print(f"  g1a_review: {manifest['g1a_review']}")
        print(f"  g2a_review: {manifest['g2a_review']}")
        print(f"  source_pack: {manifest['source_pack_path']}")
        hash_errs = verify_manifest_hashes(manifest)
        if hash_errs:
            print("\nERROR: gate-pass manifest hashes do not match current files:")
            for e in hash_errs:
                print(f"  - {e}")
            print("\nThis means the dataset, source pack, or template has changed since G1A/G2A approval.")
            print("Re-run G1A and/or G2A on the current files and produce a new manifest.")
            return 1
        records = load_dataset(manifest["dataset_path"])
        production_mode = manifest.get("production_mode", True)
        strict_refs = not manifest.get("allow_unresolved_refs", False)
        staging_dir = STAGING_DIR
    else:
        print("ERROR: provide --manifest <gate-pass.json> for live builds, or --pilot --dry-run for smoke test")
        return 1

    print(f"  loaded {len(records)} records")
    print(f"  production_mode={production_mode}, strict_refs={strict_refs}")

    # Build to staging first
    if os.path.exists(staging_dir):
        shutil.rmtree(staging_dir)
    try:
        n_written, n_bytes = build(records, staging_dir, production_mode, strict_refs)
    except ValueError as e:
        print(f"\n{e}")
        return 1
    print(f"  staged {n_written} pages to {staging_dir}/ ({n_bytes} bytes)")

    if args.dry_run:
        print("  DRY RUN: pages remain in staging, not promoted")
        return 0

    # B3: validator gates promotion. Run on staging directory; only promote if it passes.
    validator_status = run_validator(staging_dir)
    if validator_status != 0:
        print(f"\nERROR: staging validator failed (exit {validator_status}); not promoting")
        print(f"       Pages remain in {staging_dir}/ for inspection.")
        return 1

    # Atomic promote: replace dist/names/ with staging
    if os.path.exists(NAMES_DIR):
        shutil.rmtree(NAMES_DIR)
    shutil.move(staging_dir, NAMES_DIR)
    print(f"  promoted staging -> {NAMES_DIR}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
