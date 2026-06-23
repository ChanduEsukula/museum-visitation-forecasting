# Google Trends Notes

## Scope

This branch focuses on **Avila Adobe** as the single museum for the marketing/Google Trends lane. A small benchmark set is included only for context, not as the primary analysis target.

The working research question is no longer just "does search interest correlate with visitors?" It is now also:
- Which unmet-demand keywords look like missed ad or content opportunities for Avila Adobe?
- How could a government-run historic site inside a larger cultural district position itself more like a destination rather than a passive walk-through stop?

## Keyword Strategy

The keyword list in `data/raw/trends/keywords.csv` is organized around:
- `museum_specific`: Avila Adobe brand and historical-significance terms
- `discovery_marketing`: top-of-funnel tourism, rainy-day, family, lifestyle/history, short-visit, and seasonal terms
- `benchmark`: a small comparison set (`Getty Museum`, `La Brea Tar Pits`, `Griffith Observatory`)

## Build Outputs

The current pipeline writes:
- `data/raw/trends/trends_weekly_long.csv`: cached raw Google Trends pull
- `data/raw/trends/trends_fetch_meta.json`: fetch metadata
- `data/processed/trends_monthly_long.csv`: monthly long-format dataset
- `data/processed/trends_monthly.csv`: monthly wide-format modeling dataset
- `data/processed/avila_trends_monthly_dataset.csv`: presentation-friendly month-by-keyword dataset formatted like the original museum CSV

## Current Coverage

- Geo target: `US-CA`
- Current strategy: build a trends dataset that can support both historical visitor alignment and a separate 2025 opportunity scan

## Notes

- Google Trends values are normalized per term on a 0-100 scale and should be interpreted as relative search interest, not raw search volume.
- The script fetches one term at a time so each term can be analyzed independently against Avila Adobe visitation.
- If Google returns HTTP 429 rate limits after a successful raw pull, rerun the script with `--use-existing-raw` to rebuild processed monthly outputs from the cached raw CSV.
- If a longer pull is interrupted, rerun with `--resume-existing-raw` so the script skips terms already saved in the raw CSV and continues the remaining fetch.
