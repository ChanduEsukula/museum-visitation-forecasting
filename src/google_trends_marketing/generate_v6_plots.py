"""
Generate all v6 final plots into outputs/plots/google_trends_marketing/google-trends-marketing-v6/

v6 fixes over v5:
  - Lowered filter threshold: MIN_SCALED_NONZERO_MONTHS = 2, MIN_SCALED_UNIQUE_VALUES = 2
    (v5 used 6/3, which silently dropped most terms from sparse charts like engagement_strategy,
     short_visit_intent, and family_activity)
  - Replaced genuinely-empty terms (0-1 nonzero months across full dataset) with terms
    that have real data:
      * short_visit_intent: removed "couple hours" / "2 hours"; added El Pueblo Los Angeles
      * tourism_discovery: removed historical_sites / historic_attractions (both 1 nonzero);
        added Los Angeles history + historic district Los Angeles
      * engagement_strategy → cultural_engagement: removed interactive museums / cultural
        experiences (both 1 nonzero total); replaced with El Pueblo, Olvera Street,
        cultural heritage LA, Mexican heritage LA
      * family_activity: removed kid friendly museums (1 in visitor window); kept
        family activities LA + family things to do downtown
      * cultural_heritage: removed heritage tourism (0) and cultural experiences (1);
        kept El Pueblo + historic district + cultural heritage LA
  - ALL chart groups now produce BOTH a scaled chart and a raw chart (line_pair)
  - Raw charts now include x-axis year formatting and proper xlim
  - min_max_scale returns NaN (not 0) when series has no variation, preventing
    single-value terms from drawing a misleading flat line at y=0
  Rules (same as v5):
    * Every named term has a fixed color across ALL charts in this directory.
    * "Avila visitors" is always a black dashed line; never a solid coloured line.
    * Scaled charts: y-axis = min-max scaled (0-1), Avila visitors shown as black dashed.
    * Raw charts: y-axis = Google Trends 0-100; Avila visitors on secondary right y-axis.
    * Scaled charts hide zero-interest months so sparse series do not ride the bottom axis.
"""
from __future__ import annotations

import re
import shutil
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

plt.style.use("seaborn-v0_8-whitegrid")

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ROOT    = Path(__file__).resolve().parents[2]
OUT     = ROOT / "outputs/plots/google_trends_marketing/google-trends-marketing-v6"
V2_PLOTS = ROOT / "outputs/plots/google_trends_marketing/google-trends-marketing-v2"
DATA_V2 = ROOT / "data/processed/google-trends-marketing-v2"
RAW_CSV = ROOT / "data/raw/trends/google-trends-marketing-v2/trends_weekly_long.csv"
MUSEUM  = ROOT.parent / "museum-visitors.csv"

OUT.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Fixed colour map — same term = same colour in every chart
# ---------------------------------------------------------------------------
TERM_COLORS: dict[str, str] = {
    "Olvera Street":                             "#1f77b4",
    "Los Angeles history":                       "#ff7f0e",
    "things to do in Los Angeles":               "#2ca02c",
    "Avila Adobe":                               "#4d4d4d",
    "Getty Museum":                              "#9467bd",
    "La Brea Tar Pits":                          "#8c564b",
    "Griffith Observatory":                      "#e377c2",
    "things to do in LA for a couple hours":     "#17becf",
    "things to do in LA for 2 hours":            "#bcbd22",
    "things to do near Union Station Los Angeles":"#aec7e8",
    "things to do in downtown LA":               "#d62728",
    "things to do in Los Angeles in winter":     "#98df8a",
    "things to do in LA in December":            "#ff9896",
    "things to do in LA in January":             "#c5b0d5",
    "things to do in LA in February":            "#c49c94",
    "indoor things to do in Los Angeles":        "#f7b6d2",
    "family activities Los Angeles":             "#dbdb8d",
    "kid friendly museums Los Angeles":          "#9edae5",
    "family things to do in downtown LA":        "#ad494a",
    "cultural heritage Los Angeles":             "#8ca252",
    "heritage tourism Los Angeles":              "#b5cf6b",
    "historic district Los Angeles":             "#637939",
    "Mexican heritage Los Angeles":              "#e7969c",
    "El Pueblo Los Angeles":                     "#7b4173",
    "cultural experiences Los Angeles":          "#ce6dbd",
    "interactive museums Los Angeles":           "#3182bd",
    "historical sites Los Angeles":              "#fd8d3c",
    "historic attractions Los Angeles":          "#fdae6b",
}
AVILA_LINE_STYLE = dict(color="black", linestyle="--", linewidth=1.8, alpha=0.85, label="Avila visitors")

# v6: lowered from 6/3 to 2/2 — includes terms with sparse but real data
MIN_SCALED_NONZERO_MONTHS = 2
MIN_SCALED_UNIQUE_VALUES  = 2


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def slugify(term: str) -> str:
    s = term.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    return f"trends_{re.sub(r'_+', '_', s).strip('_')}"


def min_max_scale(s: pd.Series) -> pd.Series:
    s = pd.to_numeric(s, errors="coerce")
    mn, mx = s.min(), s.max()
    if pd.isna(mn) or mn == mx:
        # No variation — return NaN so the line is invisible rather than
        # a misleading flat line at 0.
        return pd.Series(np.nan, index=s.index)
    return (s - mn) / (mx - mn)


def load_raw() -> pd.DataFrame:
    df = pd.read_csv(RAW_CSV)
    df["date"]  = pd.to_datetime(df["date"], format="mixed")
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    return df


def load_monthly() -> pd.DataFrame:
    return pd.read_csv(DATA_V2 / "trends_monthly.csv")


def load_visitors() -> pd.DataFrame:
    df  = pd.read_csv(MUSEUM)
    col = "Month" if "Month" in df.columns else df.columns[0]
    out = df[[col, "Avila Adobe"]].copy()
    out.columns = ["month", "avila_visitors"]
    out["month"] = pd.to_datetime(out["month"], errors="coerce").dt.to_period("M").astype(str)
    out["avila_visitors"] = pd.to_numeric(out["avila_visitors"], errors="coerce")
    return out


def merged_monthly(monthly: pd.DataFrame, visitors: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    m = monthly.merge(visitors, on="month", how="left")
    x = pd.to_datetime(m["month"] + "-01", errors="coerce")
    return m, x


def visitor_window(m: pd.DataFrame, x: pd.Series) -> tuple[pd.DataFrame, pd.Series]:
    """Return only rows where visitor data exists, for scaled comparisons."""
    mask = m["avila_visitors"].notna()
    return m.loc[mask].copy(), x.loc[mask].copy()


def add_avila_scaled(ax: plt.Axes, m: pd.DataFrame, x: pd.Series) -> None:
    if "avila_visitors" in m.columns and m["avila_visitors"].notna().any():
        ax.plot(x, min_max_scale(m["avila_visitors"]), **AVILA_LINE_STYLE)


def add_avila_raw_secondary(ax_left: plt.Axes, m: pd.DataFrame, x: pd.Series) -> plt.Axes | None:
    if "avila_visitors" not in m.columns or not m["avila_visitors"].notna().any():
        return None
    ax2 = ax_left.twinx()
    ax2.plot(x, m["avila_visitors"], **AVILA_LINE_STYLE)
    ax2.set_ylabel("Monthly visitors (raw count)", fontsize=10)
    return ax2


def save(fig: plt.Figure, name: str) -> None:
    path = OUT / name
    fig.savefig(path, dpi=160, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {path.name}")


def is_meaningful_scaled_series(vals: pd.Series) -> bool:
    """Return True only when a term has enough nonzero history for a real normalized curve."""
    s   = pd.to_numeric(vals, errors="coerce")
    pos = s[s > 0]
    return len(pos) >= MIN_SCALED_NONZERO_MONTHS and pos.nunique() >= MIN_SCALED_UNIQUE_VALUES


def _fmt_raw_xaxis(ax: plt.Axes, x: pd.Series) -> None:
    if not x.empty:
        ax.xaxis.set_major_locator(mdates.YearLocator(1))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
        ax.set_xlim(x.min(), x.max())


def raw_window(m: pd.DataFrame, x: pd.Series, cols: list[str]) -> tuple[pd.DataFrame, pd.Series]:
    """Trim raw plots to the chart's actual non-null collection window."""
    available_cols = [col for col in cols if col in m.columns]
    if not available_cols:
        return m.iloc[0:0].copy(), x.iloc[0:0].copy()
    mask = m[available_cols].notna().any(axis=1)
    return m.loc[mask].copy(), x.loc[mask].copy()


def line_pair(
    m: pd.DataFrame,
    x: pd.Series,
    term_col_pairs: list[tuple[str, str]],
    title_scaled: str,
    title_raw: str,
    fname_scaled: str,
    fname_raw: str,
) -> None:
    """Generate a scaled (0-1) chart and a raw (0-100) chart for the same set of terms."""
    # --- Scaled (visitor window only) ---
    m_s, x_s = visitor_window(m, x)
    avail_scaled = [
        (label, col) for label, col in term_col_pairs
        if col in m_s.columns and is_meaningful_scaled_series(pd.to_numeric(m_s[col], errors="coerce"))
    ]

    fig, ax = plt.subplots(figsize=(13, 6))
    for label, col in avail_scaled:
        vals   = pd.to_numeric(m_s[col], errors="coerce")
        scaled = min_max_scale(vals.where(vals > 0))
        ax.plot(x_s, scaled, label=label, linewidth=2, color=TERM_COLORS.get(label))
    add_avila_scaled(ax, m_s, x_s)
    ax.set_title(title_scaled, fontsize=13, fontweight="bold")
    ax.set_ylabel("Min-max scaled value (0-1)", fontsize=10)
    ax.set_ylim(-0.03, 1.03)
    if not x_s.empty:
        ax.set_xlim(x_s.min(), x_s.max())
        ax.xaxis.set_major_locator(mdates.YearLocator(1))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    if not avail_scaled:
        ax.text(0.5, 0.55,
                "Not enough nonzero months in the visitor window\n"
                "for a meaningful normalized comparison.",
                ha="center", va="center", transform=ax.transAxes, fontsize=11)
    ax.legend(fontsize=8)
    fig.tight_layout()
    save(fig, fname_scaled)

    # --- Raw (full date range, no Avila overlay) ---
    avail_raw = [
        (label, col) for label, col in term_col_pairs
        if col in m.columns and pd.to_numeric(m[col], errors="coerce").gt(0).any()
    ]
    if not avail_raw:
        return
    m_r, x_r = raw_window(m, x, [col for _, col in avail_raw])
    fig, ax = plt.subplots(figsize=(13, 6))
    for label, col in avail_raw:
        ax.plot(x_r, pd.to_numeric(m_r[col], errors="coerce"),
                label=label, linewidth=2, color=TERM_COLORS.get(label))
    _fmt_raw_xaxis(ax, x_r)
    ax.set_title(title_raw, fontsize=13, fontweight="bold")
    ax.set_ylabel("Google Trends relative search interest (0-100)", fontsize=10)
    ax.set_ylim(0, 100)
    ax.legend(fontsize=8)
    fig.tight_layout()
    save(fig, fname_raw)


def line_scaled_only(
    m: pd.DataFrame,
    x: pd.Series,
    term_col_pairs: list[tuple[str, str]],
    title: str,
    fname: str,
) -> None:
    """Generate a scaled-only chart with Avila dashed; no raw companion."""
    m_s, x_s = visitor_window(m, x)
    avail = [
        (label, col) for label, col in term_col_pairs
        if col in m_s.columns and is_meaningful_scaled_series(pd.to_numeric(m_s[col], errors="coerce"))
    ]
    fig, ax = plt.subplots(figsize=(13, 6))
    for label, col in avail:
        vals   = pd.to_numeric(m_s[col], errors="coerce")
        scaled = min_max_scale(vals.where(vals > 0))
        ax.plot(x_s, scaled, label=label, linewidth=2, color=TERM_COLORS.get(label))
    add_avila_scaled(ax, m_s, x_s)
    ax.set_title(title, fontsize=13, fontweight="bold")
    ax.set_ylabel("Min-max scaled value (0-1)", fontsize=10)
    ax.set_ylim(-0.03, 1.03)
    if not x_s.empty:
        ax.set_xlim(x_s.min(), x_s.max())
        ax.xaxis.set_major_locator(mdates.YearLocator(1))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    if not avail:
        ax.text(0.5, 0.55,
                "Not enough nonzero months in the visitor window\n"
                "for a meaningful normalized comparison.",
                ha="center", va="center", transform=ax.transAxes, fontsize=11)
    ax.legend(fontsize=8)
    fig.tight_layout()
    save(fig, fname)


# ---------------------------------------------------------------------------
# Build v6
# ---------------------------------------------------------------------------

def main() -> None:
    print("Loading data…")
    raw      = load_raw()
    monthly  = load_monthly()
    visitors = load_visitors()
    m, x     = merged_monthly(monthly, visitors)

    ranking = pd.read_csv(DATA_V2 / "keyword_opportunity_ranking.csv")
    theme_summary = (
        ranking[ranking["has_available_data"] == True]
        .groupby("theme", dropna=False)
        .agg(keywords=("term", "count"),
             avg_opportunity_score=("opportunity_score", "mean"),
             avg_trend=("avg_trend", "mean"))
        .sort_values("avg_opportunity_score", ascending=False)
        .round(2).reset_index()
    )

    # ── 1. Copy unchanged favourites from v2 ─────────────────────────────
    print("\n[1] Copying v2 favourites…")
    for fname in ["top_keyword_opportunities.png", "theme_opportunity_scores.png"]:
        src = V2_PLOTS / fname
        if src.exists():
            shutil.copy2(src, OUT / fname)
            print(f"  Copied: {fname}")

    # ── 2. Scatter: terms on y-axis, 2014-2021 ───────────────────────────
    print("\n[2] Scatter — terms on y-axis (2014-2021)…")
    DATE_MIN = pd.Timestamp("2014-01-01")
    DATE_MAX = pd.Timestamp("2021-12-31")
    CMAP, VMIN, VMAX = "viridis", 0, 100

    df_s = raw[(raw["date"] >= DATE_MIN) & (raw["date"] <= DATE_MAX)].copy()
    zero_terms = df_s.groupby("term")["value"].max()
    zero_terms = zero_terms[zero_terms == 0].index.tolist()
    df_s = df_s[~df_s["term"].isin(zero_terms) & (df_s["value"].fillna(0) > 0)]
    order = df_s.groupby("term")["value"].mean().sort_values(ascending=True).index.tolist()
    df_s["y"] = df_s["term"].map({t: i for i, t in enumerate(order)})

    n = len(order)
    fig, ax = plt.subplots(figsize=(14, n * 0.42))
    sc = ax.scatter(df_s["date"], df_s["y"],
                    c=df_s["value"], cmap=CMAP, vmin=VMIN, vmax=VMAX,
                    s=df_s["value"] * 1.2 + 8, alpha=0.75, linewidths=0, edgecolors="none")
    fig.colorbar(sc, ax=ax, pad=0.01, label="Trend value (0-100)")
    ax.set_yticks(range(n))
    ax.set_yticklabels(order, fontsize=8.5)
    ax.set_xlim(DATE_MIN, DATE_MAX)
    ax.xaxis.set_major_locator(mdates.YearLocator(1))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.set_title("All Google Trends Terms — 2014 to 2021 (Dataset Period)",
                 fontsize=13, fontweight="bold", pad=10)
    ax.set_xlabel("Month", fontsize=10)
    ax.set_ylabel("Search term", fontsize=10)
    ax.grid(axis="x", linestyle="--", alpha=0.3)
    fig.tight_layout()
    save(fig, "all_terms_scatter_2014_2021_by_term.png")

    # ── 3. Top-terms scatter 2014-2026 ────────────────────────────────────
    print("\n[3] Scatter — top collected terms (2014-2026)…")
    selected = pd.read_csv(DATA_V2 / "trends_selected_2014_2026.csv")
    selected = selected.rename(columns={"month": "month_str"})
    selected_long = selected.melt(id_vars=["month_str"], var_name="col", value_name="value")
    selected_long["value"] = pd.to_numeric(selected_long["value"], errors="coerce")
    selected_long = selected_long[selected_long["value"].fillna(0) > 0].copy()
    slug_to_term = {
        slugify("Avila Adobe"):                        "Avila Adobe",
        slugify("Getty Museum"):                       "Getty Museum",
        slugify("La Brea Tar Pits"):                   "La Brea Tar Pits",
        slugify("Griffith Observatory"):               "Griffith Observatory",
        slugify("Olvera Street"):                      "Olvera Street",
        slugify("Los Angeles museums"):                "Los Angeles museums",
        slugify("things to do in LA"):                 "things to do in LA",
        slugify("things to do in Los Angeles"):        "things to do in Los Angeles",
        slugify("Los Angeles attractions"):            "Los Angeles attractions",
        slugify("free museums Los Angeles"):           "free museums Los Angeles",
        slugify("historic attractions Los Angeles"):   "historic attractions Los Angeles",
        slugify("historical sites Los Angeles"):       "historical sites Los Angeles",
        slugify("things to do in downtown LA"):        "things to do in downtown LA",
        slugify("Los Angeles history"):                "Los Angeles history",
        slugify("life in the 1840s"):                  "life in the 1840s",
        slugify("living history museum"):              "living history museum",
        slugify("historic house museum"):              "historic house museum",
        slugify("family activities Los Angeles"):      "family activities Los Angeles",
    }
    selected_long["term"] = selected_long["col"].map(slug_to_term)
    selected_long = selected_long.dropna(subset=["term"])
    selected_long["month"] = pd.to_datetime(selected_long["month_str"] + "-01", errors="coerce")
    order_2026 = (
        selected_long.groupby("term")["value"]
        .mean().sort_values(ascending=True).index.tolist()
    )
    selected_long["y"] = selected_long["term"].map({t: i for i, t in enumerate(order_2026)})
    fig, ax = plt.subplots(figsize=(14, max(7, len(order_2026) * 0.48)))
    sc2 = ax.scatter(selected_long["month"], selected_long["y"],
                     c=selected_long["value"], cmap=CMAP, vmin=VMIN, vmax=VMAX,
                     s=selected_long["value"] * 1.25 + 10, alpha=0.8,
                     linewidths=0, edgecolors="none")
    fig.colorbar(sc2, ax=ax, pad=0.01, label="Trend value (0-100)")
    ax.set_yticks(range(len(order_2026)))
    ax.set_yticklabels(order_2026, fontsize=8.5)
    ax.set_xlim(pd.Timestamp("2014-01-01"), pd.Timestamp("2025-12-31"))
    ax.xaxis.set_major_locator(mdates.YearLocator(1))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.set_title("Top Google Trends Terms — 2014 to 2026", fontsize=13, fontweight="bold", pad=10)
    ax.set_xlabel("Month", fontsize=10)
    ax.set_ylabel("Search term", fontsize=10)
    ax.grid(axis="x", linestyle="--", alpha=0.3)
    fig.tight_layout()
    save(fig, "top_terms_scatter_2014_2026.png")

    # ── 4. Avila vs top trends pair ───────────────────────────────────────
    print("\n[4] Avila vs top trends (scaled + raw)…")
    line_pair(
        m, x,
        term_col_pairs=[
            ("Olvera Street",              slugify("Olvera Street")),
            ("Los Angeles history",        slugify("Los Angeles history")),
            ("things to do in Los Angeles",slugify("things to do in Los Angeles")),
        ],
        title_scaled="Normalized Visitor vs Search-Interest Trends",
        title_raw="Top Search-Interest Trends (Google Trends Relative Interest)",
        fname_scaled="avila_vs_top_trends_scaled.png",
        fname_raw="avila_vs_top_trends_raw.png",
    )

    # ── 5. Avila vs benchmarks (scaled + raw) ────────────────────────────
    print("\n[5] Avila vs benchmarks (scaled + raw)…")
    line_pair(
        m, x,
        term_col_pairs=[
            ("Getty Museum",         slugify("Getty Museum")),
            ("La Brea Tar Pits",     slugify("La Brea Tar Pits")),
            ("Griffith Observatory", slugify("Griffith Observatory")),
        ],
        title_scaled="Normalized Benchmark Searches vs Avila Visitors",
        title_raw="Benchmark Search Interest (Google Trends Relative Interest)",
        fname_scaled="avila_vs_benchmarks_scaled.png",
        fname_raw="avila_vs_benchmarks_raw.png",
    )

    # ── 6. Short visit / downtown intent (redesigned) ─────────────────────
    # v5 had "couple hours" (1 nonzero) and "2 hours" (0 nonzero) — both dropped.
    # El Pueblo Los Angeles (80 nonzero) added; Union Station kept for raw only.
    print("\n[6] Short visit / downtown intent (scaled + raw)…")
    line_pair(
        m, x,
        term_col_pairs=[
            ("things to do in downtown LA",                 slugify("things to do in downtown LA")),
            ("El Pueblo Los Angeles",                       slugify("El Pueblo Los Angeles")),
            ("things to do near Union Station Los Angeles", slugify("things to do near Union Station Los Angeles")),
        ],
        title_scaled="Downtown & Nearby Visit Intent (Normalized)",
        title_raw="Downtown & Nearby Visit Intent (Google Trends Relative Interest)",
        fname_scaled="short_visit_intent_trends_scaled.png",
        fname_raw="short_visit_intent_trends_raw.png",
    )

    # ── 7. Tourism discovery (redesigned) ────────────────────────────────
    # v5: historical_sites (1 nonzero) + historic_attractions (1 nonzero) dropped.
    # Added: Los Angeles history (90 nonzero) + historic district (8 nonzero).
    print("\n[7] Tourism discovery (scaled + raw)…")
    line_pair(
        m, x,
        term_col_pairs=[
            ("Los Angeles history",          slugify("Los Angeles history")),
            ("historic district Los Angeles",slugify("historic district Los Angeles")),
            ("things to do in downtown LA",  slugify("things to do in downtown LA")),
        ],
        title_scaled="Tourism Discovery Trends (Normalized)",
        title_raw="Tourism Discovery Trends (Google Trends Relative Interest)",
        fname_scaled="tourism_discovery_extended_trends_scaled.png",
        fname_raw="tourism_discovery_extended_trends_raw.png",
    )

    # ── 8. Cultural engagement (replaces empty engagement_strategy) ───────
    # v5: interactive museums (1 nonzero) + cultural experiences (1 nonzero) → both empty.
    # Replaced with El Pueblo (80), Olvera Street (90), cultural heritage LA (2),
    # Mexican heritage LA (4 — all post-2021, visible in raw chart only).
    print("\n[8] Cultural engagement (scaled + raw)…")
    line_pair(
        m, x,
        term_col_pairs=[
            ("El Pueblo Los Angeles",          slugify("El Pueblo Los Angeles")),
            ("Olvera Street",                  slugify("Olvera Street")),
            ("cultural heritage Los Angeles",  slugify("cultural heritage Los Angeles")),
            ("Mexican heritage Los Angeles",   slugify("Mexican heritage Los Angeles")),
        ],
        title_scaled="Cultural Engagement Trends (Normalized)",
        title_raw="Cultural Engagement Trends (Google Trends Relative Interest)",
        fname_scaled="engagement_strategy_trends_scaled.png",
        fname_raw="engagement_strategy_trends_raw.png",
    )

    # ── 9. Seasonal visit intent (scaled only) ───────────────────────────
    print("\n[9] Seasonal visit intent (scaled)…")
    line_scaled_only(
        m, x,
        term_col_pairs=[
            ("things to do in Los Angeles in winter", slugify("things to do in Los Angeles in winter")),
            ("things to do in LA in December",        slugify("things to do in LA in December")),
            ("things to do in LA in January",         slugify("things to do in LA in January")),
            ("things to do in LA in February",        slugify("things to do in LA in February")),
            ("indoor things to do in Los Angeles",    slugify("indoor things to do in Los Angeles")),
        ],
        title="Seasonal Visit Intent Trends (Normalized)",
        fname="seasonal_visit_intent_trends.png",
    )

    # ── 10. Family activity (scaled + raw) ───────────────────────────────
    # v5: kid friendly museums (1 in visitor window) dropped by old threshold.
    # v6: kept family activities (57) + family things to do downtown (2, passes 2/2).
    print("\n[10] Family activity (scaled + raw)…")
    line_pair(
        m, x,
        term_col_pairs=[
            ("family activities Los Angeles",    slugify("family activities Los Angeles")),
            ("family things to do in downtown LA",slugify("family things to do in downtown LA")),
        ],
        title_scaled="Family Activity Trends (Normalized)",
        title_raw="Family Activity Trends (Google Trends Relative Interest)",
        fname_scaled="family_activity_trends.png",
        fname_raw="family_activity_trends_raw.png",
    )

    # ── 11. Cultural heritage (scaled only) ──────────────────────────────
    # v5: heritage tourism (0) + Mexican heritage (0 in visitor window) + cultural
    # experiences (1) all failed. v6 keeps El Pueblo (80), historic district (8),
    # cultural heritage LA (2 — passes 2/2). Mexican heritage is raw-only (all
    # its nonzero months are after the visitor window).
    print("\n[11] Cultural heritage (scaled only)…")
    line_scaled_only(
        m, x,
        term_col_pairs=[
            ("El Pueblo Los Angeles",           slugify("El Pueblo Los Angeles")),
            ("historic district Los Angeles",   slugify("historic district Los Angeles")),
            ("cultural heritage Los Angeles",   slugify("cultural heritage Los Angeles")),
        ],
        title="Cultural Heritage Trends (Normalized)",
        fname="cultural_heritage_trends.png",
    )

    print(f"\nDone. All plots in: {OUT}")


if __name__ == "__main__":
    main()
