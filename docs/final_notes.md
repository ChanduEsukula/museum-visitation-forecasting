# Final Notes — Google Trends Data Collection

## Section 1 — Dropped Terms

The drop terms from RAW into our final dataset includes two specific search parameters, meaning Google Trends didn't collect data. The dataset ran and there was an OK, but it just wrote zeros from Google Trends because these weren't searches during this time period or it just didn't collect the data — it was too small. This includes terms like `kids activities downtown Los Angeles` where Google Trends just didn't have the data. This along with the other ones we dropped because they were just too specific. I was very curious to see if they would come up with data.

**Terms dropped (returned all zeros / no search interest):**
- `1840s Los Angeles`
- `kids activities downtown Los Angeles`

## Section 2 — Google Trends Data Collection Process

That process is difficult because Google Trends doesn't have API docs. I just found forums — cite a source here as well — that says come back in 16 hours, because that's exactly what I had to do each time I was trying to aggregate data. There was a limit and we can look back on the limits for how much data we could collect with the Python script, but it was a bit frustrating for sure.

**Forum reference:** [pytrends GitHub Issues — 429 rate limiting / "come back in X hours"](https://github.com/GeneralMills/pytrends/issues)

## Section 3 — Top Theme Opportunity Scores (≥ 30)

The top available terms from our dataset are grouped by theme. Three themes came in with an average opportunity score of 30 or higher:

| Theme | Avg Opportunity Score |
|---|---|
| competitor | 50.05 |
| tourism_discovery | 42.63 |
| lifestyle_history | 30.07 |

These themes — plus the top Avila Adobe correlators from the visitor data — make up the 18 terms selected for the extended 2014–2026 dataset (`trends_selected_2014_2026.csv`).

**Top Avila Adobe correlators included:**
- `Los Angeles history` (r = 0.824)
- `Olvera Street` (r = 0.774)
- `things to do in Los Angeles` (r = 0.714)
- `Los Angeles museums` (r = 0.528)
- `family activities Los Angeles` (r = 0.432)

## Section 4 — Plot Scaling Notes

Some of the theme line charts use raw Google Trends values (0-100) and some use min-max scaling. This matters because min-max scaling hides how much more searched one term is compared to another. For example, `things to do in downtown LA` under short visit intent is probably much more searched than the other terms in that group, but when you scale everything to 0-1 it looks like they're all in the same realm. So for the charts where relative search volume is part of the story — specifically short visit intent, extended tourism discovery, and engagement strategy — we use raw Google Trends values so the spikes, the dip during COVID, and the dominant terms all show up as they actually are. For the charts where we're comparing shapes across terms with very different baselines (like seasonal visit intent or family activity), we keep the normalized version so the seasonal curves are still readable.

Google Trends does not give actual search counts in this pull. What it gives us is relative search interest on a 0-100 scale inside each term comparison. So the raw charts are not literal numbers of searches. They are the direct Google Trends values before we do any min-max scaling.

The scaled charts are the only place where Avila visitors should be compared against search interest, because those are two different units. In the scaled charts, Avila visitors are shown as a black dashed line on the same 0-1 scale. In the raw Google Trends charts, Avila visitors are not overlaid.

## Section 5 — Final Datasets

| File | Terms | Period | Notes |
|---|---|---|---|
| `trends_all_2014_2021.csv` | 40 | 2014-01 → 2021-12 | Matches museum visitor dataset window; 3 terms with zero values in this period excluded |
| `trends_selected_2014_2026.csv` | 18 | 2014-01 → 2025-12 | Top 3 themes + top Avila correlators |
| `trends_all_collected_monthly_long.csv` | 43 | 2014-01 → 2025-12 | Consolidated long-format copy of everything collected from the raw Google Trends pull |

**Final v6 plots:**
- `all_terms_scatter_2014_2021_by_term.png` — 40 terms with real data in the dataset period, x-axis capped at 2021-12-31
- `top_terms_scatter_2014_2026.png` — the top collected terms with 2014–2026 coverage, shown in the same scatter style so the labels stay readable
- `*_scaled.png` charts are the normalized comparison versions with Avila visitors as the black dashed line
- `*_raw.png` charts are the raw Google Trends relative-interest versions with no Avila visitor overlay

Note: 3 terms (`heritage tourism Los Angeles`, `historical sites Los Angeles`, `things to do in LA for 2 hours`) only have data from mid-2021 onward — they were in the backfill batch, not the original 2014–2021 fetch — so they show as blank in the dataset-period scatter and are excluded from it.

For the raw line charts in `google-trends-marketing-v6`, the x-axis is capped to the actual non-null collection window for the terms in that chart. Example: `avila_vs_top_trends_raw.png` ends at `2021-06` because those project-period terms were only collected through the original 2014–2021 dataset window.
