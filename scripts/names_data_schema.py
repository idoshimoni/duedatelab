"""
NameRecord data schema for the DueDateLab names cluster.

Per `feedback_names_no_scraping.md` and Phase 2 plan §4.4: every name's
data row tracks per-field provenance + confidence + last_reviewed.
SSA is the only safe automated source. Meaning, origin, pronunciation,
cultural notes require an explicit citable source per field. No
paraphrasing competitor copy.

Pass criteria for G1A Source/Data Licensing Gate:
- per-field provenance documented (source URL or 'SSA-public-data')
- no copied editorial expression
- taxonomy is original
- pages with no defensible field set don't ship

Note on gender_bucket: SSA reflects recorded sex at birth, not gender
identity. The bucket is a conventional grouping for navigation, not a
claim about an individual's identity.

Per Step 2 close-out review (2026-04-26):
- R1: SSA values are range-validated (year >= 1880, rank 0|1-1000, count >= 0)
- R3: production_mode requires >=2 useful content modules
- R9: KNOWN_SOURCES loaded from audit/source-packs/known-sources.json

Schema versioning: bump SCHEMA_VERSION when fields change.
"""

import json
import os
import re
import unicodedata
from dataclasses import dataclass, field, asdict
from datetime import date
from typing import Optional, List, Dict

SCHEMA_VERSION = "1.3.0"

# Per R9: source registry lives in JSON, not Python.
_SOURCES_JSON = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "audit", "source-packs", "known-sources.json"
)

def _load_known_sources():
    """Load the vetted source registry from disk. Falls back to the SSA-only
    minimum if the file is missing (e.g. during smoke tests on a clean
    checkout) but emits a warning."""
    try:
        with open(_SOURCES_JSON, "r", encoding="utf-8") as f:
            return json.load(f).get("sources", {})
    except FileNotFoundError:
        return {
            "SSA": {
                "label": "U.S. Social Security Administration baby names",
                "url": "https://www.ssa.gov/oact/babynames/",
                "license": "U.S. government public domain (Title 17 §105)",
                "scope": "U.S. popularity ranks and counts only.",
            }
        }


KNOWN_SOURCES = _load_known_sources()

# Allowed values for enumerated fields.
# Per R review §4.1: "varies by period" reads more naturally than
# "historically-mixed" for cross-period gender drift.
GENDER_BUCKETS = {"girl", "boy", "gender-neutral", "varies-by-period"}
CONFIDENCE_LEVELS = {"high", "medium", "uncertain"}

# SSA data starts in 1880 per the Social Security Administration's published
# baby names dataset (https://www.ssa.gov/oact/babynames/limits.html).
SSA_EARLIEST_YEAR = 1880
SSA_MAX_RANK = 1000


@dataclass
class FieldProvenance:
    """Provenance metadata for any data field that originated from an
    external source. Required for every meaning, origin, pronunciation,
    and cultural-note field. NOT required for SSA-public-data popularity
    fields (their source is implicit)."""
    source_id: str          # Must be a key in KNOWN_SOURCES
    source_url: str         # The specific URL the field came from
    license: str            # Permitted category: public-domain | open-license | permission | source-facts-only | short-quote-commentary
    accessed_on: str        # ISO date when the curator captured this
    confidence: str         # 'high' | 'medium' | 'uncertain'
    notes: str = ""         # Optional: caveats, scope, or original-language quotes


@dataclass
class SSAPopularityYear:
    """One year of SSA U.S. popularity data, per recorded sex.
    Per B4: recorded_sex is the SSA-recorded series identifier ('F'|'M').
    SSA publishes M and F series separately; a name with usage in both
    series carries two SSAPopularityYear rows for the same year."""
    year: int
    recorded_sex: str       # 'F' | 'M'
    rank: int               # 0 if not in top-1000 that year, else 1-1000
    count: int              # raw birth count, non-negative


@dataclass
class NameRecord:
    """One name leaf entry. Drives the `/names/<slug>/` page."""
    # Required core fields
    name: str
    slug: str
    gender_bucket: str      # One of GENDER_BUCKETS
    last_reviewed: str      # ISO date

    # gender_bucket derivation note (per R review §4.1)
    gender_bucket_rationale: str = ""  # Curator's basis: "SSA-majority", "manual", "documented-tradition"

    # Optional sourced fields. If present, MUST have provenance.
    meaning: Optional[str] = None
    meaning_provenance: Optional[FieldProvenance] = None
    origins: List[str] = field(default_factory=list)
    origins_provenance: Optional[FieldProvenance] = None
    pronunciation: Optional[str] = None
    pronunciation_provenance: Optional[FieldProvenance] = None
    cultural_notes: Optional[str] = None
    cultural_notes_provenance: Optional[FieldProvenance] = None

    # Optional editorial fields (no external source needed; these are
    # internal links / suggestions derived from the data set itself).
    variants: List[str] = field(default_factory=list)
    related_names: List[str] = field(default_factory=list)
    sibling_suggestions: List[str] = field(default_factory=list)

    # SSA popularity (public-domain, no provenance object required)
    ssa_us_top1000_years: List[SSAPopularityYear] = field(default_factory=list)
    # Per B4: when a name appears in both M and F series, primary_ssa_recorded_sex
    # tells the page which series to lead with. Other series can still surface
    # in the table.
    primary_ssa_recorded_sex: Optional[str] = None  # 'F' | 'M' | None
    ssa_latest_rank: Optional[int] = None
    ssa_latest_count: Optional[int] = None
    ssa_latest_year: Optional[int] = None

    # Schema bookkeeping
    schema_version: str = SCHEMA_VERSION


# ─── Validation ────────────────────────────────────────────────

class NameRecordValidationError(Exception):
    """Raised when a NameRecord fails G1A pre-flight validation."""


def slugify_display_name(name: str) -> str:
    """Per B9: deterministic Unicode-aware slug derivation. Handles common
    diacritics via NFKD decomposition + combining-character strip, plus
    explicit handling for characters NFKD doesn't decompose (Ø, Ł, ß, etc.).
    Hyphens in display names (Anne-Marie) are preserved through the
    non-alpha collapse. Returns ASCII lowercase a-z + 0-9 + hyphens."""
    if not name:
        return ""
    s = unicodedata.normalize("NFKD", name)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.lower()
    # Characters NFKD doesn't decompose
    s = (s.replace("ø", "o").replace("ł", "l").replace("ß", "ss")
          .replace("æ", "ae").replace("œ", "oe").replace("ð", "d").replace("þ", "th"))
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")


def _validate_slug(slug: str, display_name: str = "") -> List[str]:
    """Slug must be lowercase ASCII a-z + 0-9 + hyphens, 1-41 chars,
    starting with a letter. Per B9: slug must equal slugify_display_name(name)
    unless the source pack explicitly documents an exception."""
    errors = []
    if not slug:
        errors.append("slug is empty")
        return errors
    if not re.fullmatch(r"[a-z][a-z0-9-]{0,40}", slug):
        errors.append(
            f"slug '{slug}' must be lowercase a-z + digits + hyphens, "
            "start with a letter, and be 1-41 chars"
        )
    if display_name:
        derived = slugify_display_name(display_name)
        if derived and slug != derived:
            errors.append(
                f"slug '{slug}' does not match deterministic derivation of '{display_name}' "
                f"(expected '{derived}'). Document an explicit transliteration rule in the source pack "
                "if a different slug is intentional."
            )
    return errors


def _validate_provenance(pv: FieldProvenance, field_name: str) -> List[str]:
    errors = []
    if not pv:
        return errors
    if pv.source_id not in KNOWN_SOURCES:
        errors.append(
            f"{field_name}.provenance.source_id '{pv.source_id}' "
            f"not in KNOWN_SOURCES (loaded from {os.path.basename(_SOURCES_JSON)}). "
            f"Vet via G1A and add to known-sources.json."
        )
    if not pv.source_url or not pv.source_url.startswith(("http://", "https://")):
        errors.append(f"{field_name}.provenance.source_url must be a fetchable URL")
    if pv.confidence not in CONFIDENCE_LEVELS:
        errors.append(
            f"{field_name}.provenance.confidence '{pv.confidence}' "
            f"must be one of {sorted(CONFIDENCE_LEVELS)}"
        )
    try:
        date.fromisoformat(pv.accessed_on)
    except (ValueError, TypeError):
        errors.append(f"{field_name}.provenance.accessed_on must be ISO date")
    if not pv.license:
        errors.append(f"{field_name}.provenance.license is required")
    return errors


def _validate_ssa(rec: "NameRecord", production_mode: bool = False) -> List[str]:
    """Per R1 + B4 + B5: validate SSA value ranges, recorded_sex enum,
    and latest-field consistency."""
    errors = []
    current_year = date.today().year
    sexes_seen = set()
    # D3 (round-4 cleanup): catch accidental duplicate (year, recorded_sex)
    # rows so a curator cannot ship a name with the same row repeated, which
    # would render twice in the SSA table at scale.
    seen_year_sex = set()
    for y in rec.ssa_us_top1000_years:
        key = (y.year, y.recorded_sex)
        if key in seen_year_sex:
            errors.append(f"duplicate SSA row for {y.year}/{y.recorded_sex} in ssa_us_top1000_years")
        seen_year_sex.add(key)
    for y in rec.ssa_us_top1000_years:
        if not isinstance(y.year, int) or y.year < SSA_EARLIEST_YEAR or y.year > current_year + 1:
            errors.append(f"ssa_us_top1000_years.year {y.year} must be an integer in [{SSA_EARLIEST_YEAR}, {current_year+1}]")
        # B4: recorded_sex enum
        if y.recorded_sex not in {"F", "M"}:
            errors.append(f"ssa_us_top1000_years.recorded_sex '{y.recorded_sex}' must be 'F' or 'M'")
        else:
            sexes_seen.add(y.recorded_sex)
        if not isinstance(y.rank, int) or not (y.rank == 0 or 1 <= y.rank <= SSA_MAX_RANK):
            errors.append(f"ssa_us_top1000_years.rank {y.rank} must be 0 or 1-{SSA_MAX_RANK}")
        if not isinstance(y.count, int) or y.count < 0:
            errors.append(f"ssa_us_top1000_years.count {y.count} must be a non-negative integer")
        # B5: in production_mode, rank > 0 requires count > 0
        if production_mode and y.rank > 0 and y.count <= 0:
            errors.append(
                f"ssa_us_top1000_years entry {y.year}/{y.recorded_sex}: rank={y.rank} > 0 "
                f"requires count > 0 in production_mode (smoke fixtures may set count=0)"
            )

    # Whether SSA data is present at all (any of: row data, headline rank, headline year)
    has_ssa = bool(
        rec.ssa_us_top1000_years
        or rec.ssa_latest_rank is not None
        or rec.ssa_latest_year is not None
        or rec.ssa_latest_count is not None
    )

    # C2 (round-3): primary_ssa_recorded_sex required for ANY production SSA record,
    # not only dual-series. The headline series must be explicit so the template
    # can disambiguate the page lead and the validator can bind latest-fields to
    # the correct row.
    if production_mode and has_ssa and not rec.primary_ssa_recorded_sex:
        errors.append(
            "primary_ssa_recorded_sex is required in production_mode when SSA data is present"
        )
    # B4: when multiple sexes appear, primary_ssa_recorded_sex must be set even outside production
    if len(sexes_seen) > 1 and not rec.primary_ssa_recorded_sex:
        errors.append(
            "ssa_us_top1000_years has both F and M series; primary_ssa_recorded_sex "
            "must be set to 'F' or 'M' to indicate the page's lead series"
        )
    if rec.primary_ssa_recorded_sex and rec.primary_ssa_recorded_sex not in {"F", "M"}:
        errors.append(f"primary_ssa_recorded_sex '{rec.primary_ssa_recorded_sex}' must be 'F' or 'M'")
    if rec.primary_ssa_recorded_sex and rec.primary_ssa_recorded_sex not in sexes_seen and sexes_seen:
        errors.append(
            f"primary_ssa_recorded_sex '{rec.primary_ssa_recorded_sex}' has no rows in "
            f"ssa_us_top1000_years (sexes seen: {sorted(sexes_seen)})"
        )

    # Latest-field range checks
    if rec.ssa_latest_rank is not None:
        if not isinstance(rec.ssa_latest_rank, int) or not (1 <= rec.ssa_latest_rank <= SSA_MAX_RANK):
            errors.append(f"ssa_latest_rank {rec.ssa_latest_rank} must be 1-{SSA_MAX_RANK}")
    if rec.ssa_latest_count is not None:
        if not isinstance(rec.ssa_latest_count, int) or rec.ssa_latest_count < 0:
            errors.append(f"ssa_latest_count {rec.ssa_latest_count} must be non-negative")

    # B5: latest-field consistency
    if rec.ssa_latest_rank is not None and rec.ssa_latest_year is None:
        errors.append("ssa_latest_year is required when ssa_latest_rank is set")
    if rec.ssa_latest_count is not None and rec.ssa_latest_rank is None:
        errors.append("ssa_latest_rank is required when ssa_latest_count is set")
    if rec.ssa_latest_year is not None and rec.ssa_us_top1000_years:
        newest = max(rec.ssa_us_top1000_years, key=lambda y: y.year)
        if rec.ssa_latest_year != newest.year:
            errors.append(
                f"ssa_latest_year {rec.ssa_latest_year} must match newest "
                f"ssa_us_top1000_years.year {newest.year}"
            )

    # C1 (round-3): when ssa_latest_rank is set in production_mode, ssa_latest_count
    # must also be set and > 0. A headline rank without a headline birth count is
    # not displayable.
    if production_mode and rec.ssa_latest_rank is not None:
        if rec.ssa_latest_count is None or rec.ssa_latest_count <= 0:
            errors.append(
                "ssa_latest_count must be > 0 when ssa_latest_rank is set in production_mode"
            )

    # C1 (round-3): bind ssa_latest_rank/ssa_latest_count to the primary SSA row
    # for the latest year. The headline row must exist and its rank/count must
    # match the headline fields.
    if (
        production_mode
        and rec.ssa_latest_rank is not None
        and rec.ssa_latest_year is not None
        and rec.primary_ssa_recorded_sex
        and rec.ssa_us_top1000_years
    ):
        primary_rows = [
            y for y in rec.ssa_us_top1000_years
            if y.year == rec.ssa_latest_year
            and y.recorded_sex == rec.primary_ssa_recorded_sex
        ]
        if not primary_rows:
            errors.append(
                f"ssa_latest_year {rec.ssa_latest_year} has no row matching "
                f"primary_ssa_recorded_sex '{rec.primary_ssa_recorded_sex}' in ssa_us_top1000_years"
            )
        else:
            row = primary_rows[0]
            if row.rank != rec.ssa_latest_rank:
                errors.append(
                    f"ssa_latest_rank {rec.ssa_latest_rank} does not match primary SSA row rank {row.rank} "
                    f"({rec.ssa_latest_year}/{rec.primary_ssa_recorded_sex})"
                )
            if rec.ssa_latest_count is not None and row.count != rec.ssa_latest_count:
                errors.append(
                    f"ssa_latest_count {rec.ssa_latest_count} does not match primary SSA row count {row.count} "
                    f"({rec.ssa_latest_year}/{rec.primary_ssa_recorded_sex})"
                )
    return errors


def _content_modules(rec: "NameRecord") -> dict:
    """Return a map of which content modules this record can emit. Used by
    the production-mode minimum module check (R3)."""
    return {
        "ssa_with_depth": bool(
            rec.ssa_us_top1000_years and rec.ssa_latest_year and len(rec.ssa_us_top1000_years) >= 2
        ),
        "ssa_thin": bool(rec.ssa_latest_rank or rec.ssa_us_top1000_years),
        "meaning": bool(rec.meaning and rec.meaning_provenance),
        "origin": bool(rec.origins and rec.origins_provenance),
        "pronunciation": bool(rec.pronunciation and rec.pronunciation_provenance),
        "cultural_notes": bool(rec.cultural_notes and rec.cultural_notes_provenance),
        "related_links": bool(rec.related_names or rec.variants or rec.sibling_suggestions),
    }


def validate_record(rec: NameRecord, production_mode: bool = False) -> List[str]:
    """Return a list of validation errors. Empty list = passes pre-flight.

    `production_mode=True` enforces the stricter R3 floor: at least 2 useful
    content modules (where SSA-with-depth or any sourced descriptive field
    counts; thin-SSA-rank-only does NOT count as production-ready).
    Smoke fixtures should call with production_mode=False."""
    errors = []

    # Required fields
    if not rec.name or not rec.name.strip():
        errors.append("name is required")
    errors.extend(_validate_slug(rec.slug, rec.name))
    if rec.gender_bucket not in GENDER_BUCKETS:
        errors.append(
            f"gender_bucket '{rec.gender_bucket}' must be one of {sorted(GENDER_BUCKETS)}"
        )
    if not rec.gender_bucket_rationale and production_mode:
        errors.append(
            "gender_bucket_rationale is required in production_mode "
            "(e.g. 'SSA-majority', 'manual-review', 'documented-tradition')"
        )
    try:
        date.fromisoformat(rec.last_reviewed)
    except (ValueError, TypeError):
        errors.append("last_reviewed must be ISO date")

    # Sourced fields require provenance
    if rec.meaning and not rec.meaning_provenance:
        errors.append("meaning is set but meaning_provenance is missing")
    if rec.meaning_provenance and not rec.meaning:
        errors.append("meaning_provenance is set but meaning is missing")
    errors.extend(_validate_provenance(rec.meaning_provenance, "meaning") if rec.meaning_provenance else [])

    if rec.origins and not rec.origins_provenance:
        errors.append("origins is set but origins_provenance is missing")
    if rec.origins_provenance and not rec.origins:
        errors.append("origins_provenance is set but origins is missing")
    errors.extend(_validate_provenance(rec.origins_provenance, "origins") if rec.origins_provenance else [])

    if rec.pronunciation and not rec.pronunciation_provenance:
        errors.append("pronunciation is set but pronunciation_provenance is missing")
    if rec.pronunciation_provenance and not rec.pronunciation:
        errors.append("pronunciation_provenance is set but pronunciation is missing")
    errors.extend(_validate_provenance(rec.pronunciation_provenance, "pronunciation") if rec.pronunciation_provenance else [])

    if rec.cultural_notes and not rec.cultural_notes_provenance:
        errors.append("cultural_notes is set but cultural_notes_provenance is missing")
    if rec.cultural_notes_provenance and not rec.cultural_notes:
        errors.append("cultural_notes_provenance is set but cultural_notes is missing")
    errors.extend(_validate_provenance(rec.cultural_notes_provenance, "cultural_notes") if rec.cultural_notes_provenance else [])

    # SSA value validation (R1 + B4 + B5)
    errors.extend(_validate_ssa(rec, production_mode=production_mode))

    # B6: schema version enforcement on records (production only).
    # Smoke fixtures may carry a stale version; production_mode rejects.
    if production_mode and rec.schema_version != SCHEMA_VERSION:
        errors.append(
            f"record schema_version '{rec.schema_version}' != current '{SCHEMA_VERSION}'. "
            "Re-validate the dataset against the current schema before production build."
        )

    # Minimum publishable bar
    modules = _content_modules(rec)
    if production_mode:
        # R3: production needs >=2 useful modules. Thin SSA (rank only,
        # no multi-year depth) does NOT count by itself. Either:
        # - SSA with depth, plus at least one other module, OR
        # - Two non-SSA modules
        countable = sum([
            modules["ssa_with_depth"],
            modules["meaning"],
            modules["origin"],
            modules["pronunciation"],
            modules["cultural_notes"],
        ])
        if countable < 2:
            errors.append(
                "production record needs at least 2 useful content modules "
                "(SSA-with-depth counts as 1; meaning/origin/pronunciation/cultural_notes each count as 1; "
                "thin SSA rank without multi-year history does not count by itself)"
            )
    else:
        # Smoke/fixture mode: original lenient floor
        has_any = bool(modules["ssa_thin"]) or any(
            [modules["meaning"], modules["origin"], modules["pronunciation"], modules["cultural_notes"]]
        )
        if not has_any:
            errors.append(
                "record has neither SSA popularity nor any sourced descriptive field. "
                "Pages without either are too thin to ship."
            )

    # Variants and related_names should reference internal slugs only
    for slug_ref in rec.variants + rec.related_names + rec.sibling_suggestions:
        if not re.fullmatch(r"[a-z][a-z0-9-]{0,40}", slug_ref):
            errors.append(
                f"reference slug '{slug_ref}' must be a valid lowercase slug. "
                "Variants/related/siblings reference internal name pages by slug."
            )

    return errors


# ─── Serialization helpers ──────────────────────────────────────

def to_json(rec: NameRecord) -> str:
    """Emit a NameRecord as a single-line JSON document."""
    return json.dumps(asdict(rec), separators=(",", ":"))


def from_json(s: str) -> NameRecord:
    """Parse a NameRecord JSON document. Returns a partially-populated
    NameRecord; caller should run validate_record() before relying on it.
    Underscore-prefixed keys (e.g. _comment, _expected) are stripped before
    construction to support fixture annotations."""
    d = json.loads(s)
    d = {k: v for k, v in d.items() if not k.startswith("_")}
    if d.get("meaning_provenance"):
        d["meaning_provenance"] = FieldProvenance(**d["meaning_provenance"])
    if d.get("origins_provenance"):
        d["origins_provenance"] = FieldProvenance(**d["origins_provenance"])
    if d.get("pronunciation_provenance"):
        d["pronunciation_provenance"] = FieldProvenance(**d["pronunciation_provenance"])
    if d.get("cultural_notes_provenance"):
        d["cultural_notes_provenance"] = FieldProvenance(**d["cultural_notes_provenance"])
    if d.get("ssa_us_top1000_years"):
        d["ssa_us_top1000_years"] = [SSAPopularityYear(**y) for y in d["ssa_us_top1000_years"]]
    return NameRecord(**d)


# ─── Smoke test ─────────────────────────────────────────────────

if __name__ == "__main__":
    # Smoke test: SSA-only with valid range
    olivia = NameRecord(
        name="Olivia",
        slug="olivia",
        gender_bucket="girl",
        last_reviewed=date.today().isoformat(),
        ssa_latest_year=2024,
        ssa_latest_rank=1,
        ssa_latest_count=15117,
        ssa_us_top1000_years=[
            SSAPopularityYear(year=2024, recorded_sex="F", rank=1, count=15117),
            SSAPopularityYear(year=2023, recorded_sex="F", rank=1, count=15270),
        ],
    )
    errs = validate_record(olivia, production_mode=False)
    print(f"olivia (SSA-only, fixture mode): {len(errs)} error(s)")
    for e in errs:
        print(f"  - {e}")

    # Now try in production_mode: should fail because only 1 module (SSA-with-depth)
    errs = validate_record(olivia, production_mode=True)
    print(f"olivia (SSA-only, production mode): {len(errs)} error(s) [expected: gender_rationale + min-modules]")
    for e in errs:
        print(f"  - {e}")

    # SSA range probe
    bad_ssa = NameRecord(
        name="BadSSA",
        slug="badssa",
        gender_bucket="girl",
        last_reviewed=date.today().isoformat(),
        ssa_us_top1000_years=[SSAPopularityYear(year=3000, recorded_sex="X", rank=5000, count=-10)],
    )
    errs = validate_record(bad_ssa)
    print(f"badssa (R1+B4 range probe): {len(errs)} error(s) [expected: 4 SSA errors incl recorded_sex]")
    for e in errs:
        print(f"  - {e}")

    # Provenance without visible field
    orphan = NameRecord(
        name="Orphan",
        slug="orphan",
        gender_bucket="girl",
        last_reviewed=date.today().isoformat(),
        meaning_provenance=FieldProvenance(
            source_id="SSA", source_url="https://example.com",
            license="public domain", accessed_on="2026-04-26", confidence="high",
        ),
        ssa_latest_rank=100,
    )
    errs = validate_record(orphan)
    print(f"orphan (R1 orphaned provenance): {len(errs)} error(s) [expected: meaning_provenance set but meaning missing]")
    for e in errs:
        print(f"  - {e}")
