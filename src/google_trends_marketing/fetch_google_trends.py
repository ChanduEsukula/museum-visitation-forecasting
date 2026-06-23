"""
Download Google Trends interest-over-time for keywords listed in data/raw/trends/keywords.csv.

Each term is requested alone so the 0–100 index is scaled within that term (valid for
per-term correlation with visitation and for ad-keyword opportunity analysis). Weekly
points are aggregated to calendar-month means. The script also writes a presentation-
friendly monthly CSV that mirrors the original museum dataset style: one month column
and one column per keyword.

Requires: pip install pytrends (see requirements.txt)
"""

from __future__ import annotations

import argparse
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from pytrends.request import TrendReq


def slugify_term(term: str) -> str:
    s = term.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    return f"trends_{s}"


def fetch_term(
    term: str,
    timeframe: str,
    geo: str,
    retries: int = 3,
    sleep_s: float = 2.0,
) -> pd.DataFrame:
    """Return weekly (or daily) interest dataframe with columns date, value."""
    last_err: Exception | None = None
    for attempt in range(retries):
        try:
            pytrends = TrendReq(hl="en-US", tz=360)
            pytrends.build_payload([term], cat=0, timeframe=timeframe, geo=geo)
            df = pytrends.interest_over_time()
            if df is None or df.empty:
                return pd.DataFrame(columns=["date", "value"])
            df = df.drop(columns=["isPartial"], errors="ignore")
            if df.shape[1] != 1:
                raise RuntimeError(f"Unexpected columns for {term!r}: {list(df.columns)}")
            out = df.rename(columns={df.columns[0]: "value"}).reset_index()
            out = out.rename(columns={out.columns[0]: "date"})
            out["date"] = pd.to_datetime(out["date"])
            return out[["date", "value"]]
        except Exception as e:  # noqa: BLE001
            last_err = e
            time.sleep(sleep_s * (attempt + 1))
    raise RuntimeError(f"Failed to fetch {term!r} after {retries} tries") from last_err


def weekly_to_monthly_mean(weekly: pd.DataFrame) -> pd.DataFrame:
    """Aggregate weekly Google Trends points to calendar-month mean."""
    if weekly.empty:
        return pd.DataFrame(columns=["month", "value"])
    weekly = weekly.copy()
    weekly["date"] = pd.to_datetime(weekly["date"], errors="coerce")
    weekly["value"] = pd.to_numeric(weekly["value"], errors="coerce")
    weekly = weekly.dropna(subset=["date", "value"]).sort_values("date")
    if weekly.empty:
        return pd.DataFrame(columns=["month", "value"])
    s = weekly.set_index("date")["value"]
    monthly = s.resample("ME").mean()
    out = monthly.reset_index()
    out.columns = ["month_end", "value"]
    out["month"] = out["month_end"].dt.to_period("M").astype(str)
    return out[["month", "value"]]


def to_presentation_dataset(monthly_term_wide: pd.DataFrame) -> pd.DataFrame:
    """Return a month-by-keyword dataset styled like the Kaggle museum CSV."""
    if monthly_term_wide.empty:
        return pd.DataFrame(columns=["Month"])
    wide = monthly_term_wide.copy()
    wide = wide.rename(columns={"month": "Month"})
    wide["Month"] = pd.to_datetime(wide["Month"] + "-01").dt.strftime("%Y-%m-%dT00:00:00.000")
    value_cols = [c for c in wide.columns if c != "Month"]
    return wide[["Month", *value_cols]]


def timeframe_months(timeframe: str) -> list[str]:
    """Expand a pytrends timeframe string into monthly labels."""
    start_raw, end_raw = timeframe.split()
    start = pd.Timestamp(start_raw).to_period("M")
    end = pd.Timestamp(end_raw).to_period("M")
    return [str(p) for p in pd.period_range(start=start, end=end, freq="M")]


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch Google Trends and build monthly features.")
    parser.add_argument(
        "--keywords-csv",
        type=Path,
        default=Path("data/raw/trends/keywords.csv"),
        help="CSV with columns term,lane,theme,notes",
    )
    parser.add_argument(
        "--geo",
        default="US-CA",
        help="pytrends geo code, e.g. US-CA (California) or empty string for worldwide",
    )
    parser.add_argument(
        "--timeframe",
        default="2014-01-01 2025-12-31",
        help="Inclusive range passed to pytrends (YYYY-MM-DD YYYY-MM-DD)",
    )
    parser.add_argument(
        "--sleep",
        type=float,
        default=3.0,
        help="Seconds to wait between requests (rate limiting)",
    )
    parser.add_argument(
        "--out-raw",
        type=Path,
        default=Path("data/raw/trends/trends_weekly_long.csv"),
    )
    parser.add_argument(
        "--out-monthly-long",
        type=Path,
        default=Path("data/processed/trends_monthly_long.csv"),
    )
    parser.add_argument(
        "--out-monthly-wide",
        type=Path,
        default=Path("data/processed/trends_monthly.csv"),
    )
    parser.add_argument(
        "--meta-json",
        type=Path,
        default=Path("data/raw/trends/trends_fetch_meta.json"),
    )
    parser.add_argument(
        "--out-presentation",
        type=Path,
        default=Path("data/processed/avila_trends_monthly_dataset.csv"),
        help="Month-by-keyword CSV formatted like the original museum dataset.",
    )
    parser.add_argument(
        "--use-existing-raw",
        action="store_true",
        help="Skip API fetch and rebuild monthly outputs from an existing raw CSV.",
    )
    parser.add_argument(
        "--resume-existing-raw",
        action="store_true",
        help="Resume a partially completed raw pull by skipping terms already present.",
    )
    parser.add_argument(
        "--offset",
        type=int,
        default=0,
        help="Skip the first N pending terms after resume filtering.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Fetch at most N pending terms after offset (0 means no limit).",
    )
    parser.add_argument(
        "--continue-on-error",
        action="store_true",
        help="Log per-term failures and continue fetching the remaining chunk.",
    )
    parser.add_argument(
        "--failed-terms-csv",
        type=Path,
        default=Path("data/raw/trends/trends_failed_terms.csv"),
        help="CSV to record failed terms when using --continue-on-error.",
    )
    args = parser.parse_args()

    kw = pd.read_csv(args.keywords_csv)
    required = {"term", "lane", "theme"}
    missing = required - set(kw.columns)
    if missing:
        raise SystemExit(f"keywords.csv missing columns: {missing}")

    fetched_at = datetime.now(timezone.utc).isoformat()
    if args.use_existing_raw:
        weekly_long = pd.read_csv(args.out_raw)
    else:
        if args.resume_existing_raw and args.out_raw.exists():
            weekly_long = pd.read_csv(args.out_raw)
            completed_terms = set(weekly_long.get("term", pd.Series(dtype=str)).astype(str))
        else:
            weekly_long = pd.DataFrame()
            completed_terms: set[str] = set()

        pending_kw = kw[~kw["term"].astype(str).str.strip().isin(completed_terms)].copy()
        if args.offset:
            pending_kw = pending_kw.iloc[args.offset :]
        if args.limit:
            pending_kw = pending_kw.iloc[: args.limit]

        failed_rows: list[dict[str, str]] = []
        for _, row in pending_kw.iterrows():
            term = str(row["term"]).strip()
            if not term:
                continue
            print(f"Fetching: {term!r} …", flush=True)
            try:
                w = fetch_term(term, timeframe=args.timeframe, geo=args.geo or "")
            except Exception as exc:  # noqa: BLE001
                if not args.continue_on_error:
                    raise
                failed_rows.append({"term": term, "error": str(exc)})
                print(f"Failed and continuing: {term!r} -> {exc}", flush=True)
                continue
            w["term"] = term
            w["lane"] = row["lane"]
            w["theme"] = row["theme"]
            weekly_long = pd.concat([weekly_long, w], ignore_index=True)
            args.out_raw.parent.mkdir(parents=True, exist_ok=True)
            weekly_long.to_csv(args.out_raw, index=False)
            completed_terms.add(term)
            time.sleep(args.sleep)
        if failed_rows:
            failed_df = pd.DataFrame(failed_rows)
            args.failed_terms_csv.parent.mkdir(parents=True, exist_ok=True)
            failed_df.to_csv(args.failed_terms_csv, index=False)

    monthly_parts: list[pd.DataFrame] = []
    for term in kw["term"].astype(str).str.strip().unique():
        if not term:
            continue
        sub = weekly_long[weekly_long["term"] == term]
        m = weekly_to_monthly_mean(sub[["date", "value"]])
        m["term"] = term
        meta = kw[kw["term"].astype(str).str.strip() == term].iloc[0]
        m["lane"] = meta["lane"]
        m["theme"] = meta["theme"]
        m["geo"] = args.geo
        m["source"] = "Google Trends via pytrends"
        m["notes"] = meta["notes"] if "notes" in kw.columns else ""
        monthly_parts.append(m)

    monthly_long = pd.concat(monthly_parts, ignore_index=True) if monthly_parts else pd.DataFrame()
    args.out_monthly_long.parent.mkdir(parents=True, exist_ok=True)
    monthly_long.to_csv(args.out_monthly_long, index=False)

    all_terms = kw["term"].astype(str).str.strip()
    all_terms = [term for term in all_terms if term]
    all_months = timeframe_months(args.timeframe)

    if monthly_long.empty:
        wide = pd.DataFrame({"month": all_months})
    else:
        wide = monthly_long.pivot_table(
            index="month",
            columns="term",
            values="value",
            aggfunc="mean",
        ).reset_index()
        wide = wide.set_index("month").reindex(all_months).reset_index()
    for term in all_terms:
        if term not in wide.columns:
            wide[term] = pd.NA
    wide = wide[["month", *all_terms]]
    rename = {c: slugify_term(c) for c in wide.columns if c != "month"}
    wide = wide.rename(columns=rename)
    wide.to_csv(args.out_monthly_wide, index=False)
    presentation_wide = wide.rename(columns={slugify_term(term): term for term in all_terms})
    presentation = to_presentation_dataset(presentation_wide)
    args.out_presentation.parent.mkdir(parents=True, exist_ok=True)
    presentation.to_csv(args.out_presentation, index=False)

    meta = {
        "fetched_at_utc": fetched_at,
        "geo": args.geo,
        "timeframe": args.timeframe,
        "keywords_file": str(args.keywords_csv),
        "n_terms": int(kw["term"].astype(str).str.strip().ne("").sum()),
        "out_raw": str(args.out_raw),
        "out_monthly_long": str(args.out_monthly_long),
        "out_monthly_wide": str(args.out_monthly_wide),
        "out_presentation": str(args.out_presentation),
    }
    args.meta_json.parent.mkdir(parents=True, exist_ok=True)
    args.meta_json.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(
        "Wrote:",
        args.out_raw,
        args.out_monthly_long,
        args.out_monthly_wide,
        args.out_presentation,
        args.meta_json,
    )


if __name__ == "__main__":
    main()
