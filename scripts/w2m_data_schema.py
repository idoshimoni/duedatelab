"""
Weeks-to-months data schema and deterministic record generator.

Phase 2 Step 5 (Option B), pregnancy weeks-to-months programmatic
per-week leaves. Architecture LOCKED 2026-04-29 per round 1.5
research-AI consult — see auto-memory/project_step5_w2m_architecture_locked.md.

This module contains:
  1. The W2MRecord dataclass, one record per week (1..42).
  2. build_records() which deterministically generates all 42.
  3. Pure arithmetic helpers used by the template and the verifier.

There is no external dataset and no source pack. Inputs are the
integer week numbers 1..42. Outputs are deterministic floats and
strings. G1A-lite is satisfied by this property: the data is
arithmetic, not licensed content.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional

# Schema version, bump when record shape changes.
SCHEMA_VERSION = "1.0.0"

# Average calendar month in days. 365.25 / 12 = 30.4375.
AVG_CALENDAR_MONTH_DAYS = 30.4375

# Convention constant: 1 four-week pregnancy month = 28 days.
FOUR_WEEK_MONTH_DAYS = 28

# Inclusive range of weeks generated.
MIN_WEEK = 1
MAX_WEEK = 42

# Edge-week handling per round 1.5 reply: weeks 1-3 carry an
# LMP-counting note explicitly, because LMP-based dating counts
# weeks before pregnancy has technically occurred.
LMP_NOTE_THRESHOLD = 3


@dataclass(frozen=True)
class W2MRecord:
    """One deterministic record for week N of pregnancy.

    All fields are derived from `week` plus the convention constants.
    No external lookups, no random values, no time-dependent fields
    (the build date is stamped at render time, not on the record).
    """
    week: int
    days_since_lmp: int
    four_week_months: float
    completed_4w_months: int
    remaining_weeks_after_4w: int
    calendar_months_avg: float
    is_lmp_counted: bool
    prev_week: Optional[int]
    next_week: Optional[int]

    # Display-ready strings, computed once at record creation so
    # template render is purely substitution.
    four_week_months_str: str
    calendar_months_str: str
    days_str: str
    completed_remainder_str: str
    hero_answer: str
    title: str
    h1: str
    meta_description: str
    canonical_url: str

    # SEO/UX strings used by the breadcrumb and table tag.
    breadcrumb_position3_name: str
    table_tag_html: str  # "" for non-LMP weeks, " <span class='pl-w2m-tag'>...</span>" for weeks 1-3

    schema_version: str = SCHEMA_VERSION


def _format_four_week_months(four_week_months: float) -> str:
    """Render the four-week-month decimal cleanly:
       7.0 -> "7", 5.75 -> "5.75", 0.5 -> "0.5", 1.25 -> "1.25"."""
    if four_week_months == int(four_week_months):
        return str(int(four_week_months))
    # Up to 2 decimals, strip trailing zeros.
    s = f"{four_week_months:.2f}".rstrip("0").rstrip(".")
    return s


def _four_week_unit(four_week_months: float) -> str:
    """Return 'month' or 'months' based on the four-week-month count.

    Per round 4 reviewer F2 must-fix: when the count is exactly 1.0,
    use the singular 'month' to avoid 'X four-week pregnancy months'
    where X = 1.
    """
    return "month" if four_week_months == 1.0 else "months"


def _format_completed_remainder(completed: int, remaining_weeks: int) -> str:
    """Render the human-readable completed + remainder string.

    Examples:
        (1, 0) -> "1 four-week month"
        (7, 0) -> "7 four-week months"
        (5, 3) -> "5 four-week months + 3 weeks"
        (0, 2) -> "0 four-week months + 2 weeks"
        (1, 1) -> "1 four-week month + 1 week"
    """
    month_word = "month" if completed == 1 else "months"
    base = f"{completed} four-week {month_word}"
    if remaining_weeks == 0:
        return base
    week_word = "week" if remaining_weeks == 1 else "weeks"
    return f"{base} + {remaining_weeks} {week_word}"


def _format_hero_answer(week: int, four_week_months: float,
                       four_week_months_str: str,
                       completed_remainder_str: str,
                       calendar_months_str: str, days: int) -> str:
    """Render the leaf hero-answer line per round 1.5 spec.

    Whole-month weeks (4, 8, 12, ..., 40) drop the "or N four-week months
    + 0 weeks" clause because it adds nothing. Other weeks include it.

    Per round 4 reviewer F2 must-fix: pluralize 'month'/'months' based
    on the four-week-month count to avoid '1 four-week pregnancy months'.
    """
    week_word = "week" if week == 1 else "weeks"
    unit = _four_week_unit(four_week_months)
    if week % 4 == 0:
        return (
            f"{week} {week_word} = {four_week_months_str} "
            f"four-week pregnancy {unit}. That is about "
            f"{calendar_months_str} average calendar months and "
            f"{days} days since LMP."
        )
    return (
        f"{week} {week_word} = {four_week_months_str} "
        f"four-week pregnancy {unit}, or {completed_remainder_str}. "
        f"That is about {calendar_months_str} average calendar months "
        f"and {days} days since LMP."
    )


def _format_meta_description(week: int, four_week_months: float,
                            four_week_months_str: str,
                            calendar_months_str: str, days: int) -> str:
    """Per-leaf meta description, unique by week.

    Per round 4 reviewer F2 must-fix: pluralize 'month'/'months' based
    on the four-week-month count.
    """
    week_word = "week" if week == 1 else "weeks"
    unit = _four_week_unit(four_week_months)
    return (
        f"{week} {week_word} pregnant in months: {four_week_months_str} "
        f"four-week pregnancy {unit}, about {calendar_months_str} average "
        f"calendar months, {days} days since LMP. Includes the conversion "
        f"convention and a chart of surrounding weeks."
    )


def make_record(week: int) -> W2MRecord:
    """Build the deterministic record for a given week.

    Args:
        week: integer in [MIN_WEEK, MAX_WEEK].

    Returns:
        W2MRecord with all fields populated.

    Raises:
        ValueError if week is outside the supported range.
    """
    if not isinstance(week, int):
        raise ValueError(f"week must be an int, got {type(week).__name__}")
    if week < MIN_WEEK or week > MAX_WEEK:
        raise ValueError(f"week must be in [{MIN_WEEK}, {MAX_WEEK}], got {week}")

    days = week * 7
    four_week = days / FOUR_WEEK_MONTH_DAYS
    completed = days // FOUR_WEEK_MONTH_DAYS
    remaining_days = days - completed * FOUR_WEEK_MONTH_DAYS
    remaining_weeks = remaining_days // 7  # always exact since days is week*7
    calendar = days / AVG_CALENDAR_MONTH_DAYS
    is_lmp = week <= LMP_NOTE_THRESHOLD

    four_week_str = _format_four_week_months(four_week)
    calendar_str = f"{calendar:.1f}"
    days_str = str(days)
    completed_remainder_str = _format_completed_remainder(completed, remaining_weeks)
    hero = _format_hero_answer(week, four_week, four_week_str,
                               completed_remainder_str, calendar_str, days)
    week_word = "Week" if week == 1 else "Weeks"
    week_word_lower = "week" if week == 1 else "weeks"
    title = f"{week} {week_word} Pregnant in Months | DueDateLab"
    h1 = f"{week} {week_word_lower} pregnant in months"
    meta = _format_meta_description(week, four_week, four_week_str, calendar_str, days)
    canonical = f"https://duedatelab.com/pregnancy/weeks-to-months/{week}/"
    crumb3 = f"{week} {week_word} Pregnant in Months"
    table_tag = (
        ' <span class="pl-w2m-tag" title="LMP-counted early dating week">LMP-counted</span>'
        if is_lmp else ""
    )

    return W2MRecord(
        week=week,
        days_since_lmp=days,
        four_week_months=round(four_week, 4),
        completed_4w_months=completed,
        remaining_weeks_after_4w=remaining_weeks,
        calendar_months_avg=round(calendar, 4),
        is_lmp_counted=is_lmp,
        prev_week=week - 1 if week > MIN_WEEK else None,
        next_week=week + 1 if week < MAX_WEEK else None,
        four_week_months_str=four_week_str,
        calendar_months_str=calendar_str,
        days_str=days_str,
        completed_remainder_str=completed_remainder_str,
        hero_answer=hero,
        title=title,
        h1=h1,
        meta_description=meta,
        canonical_url=canonical,
        breadcrumb_position3_name=crumb3,
        table_tag_html=table_tag,
        schema_version=SCHEMA_VERSION,
    )


def descriptive_adjacent_anchor_text(target_week: int) -> str:
    """Anchor text for prev/next links per round-2 Q8 must-fix.

    Returns descriptive text like "22 weeks pregnant in months" rather
    than generic "Previous" / "← Week 22".
    """
    week_word = "week" if target_week == 1 else "weeks"
    return f"{target_week} {week_word} pregnant in months"


def build_all_records() -> list[W2MRecord]:
    """Generate the full set of 42 records in week order."""
    return [make_record(w) for w in range(MIN_WEEK, MAX_WEEK + 1)]
