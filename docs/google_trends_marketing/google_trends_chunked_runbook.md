# Google Trends Chunked Runbook

## Current State

- `python_v1` is the current working run to build from.
- `python_v1` currently uses `geo=US-CA`, not worldwide.
- Missing terms in the ranking usually mean the automated fetch did not successfully return data for that term yet, most often because Google Trends returned `429`.
- The cleanest current dataset with no empty columns is:
  - `data/processed/python_v1/trends_monthly_available_only.csv`

## Activate Environment

```bash
cd "<local_path_redacted>"
source .venv/bin/activate
```

## Rebuild The Current `python_v1` Outputs From Cached Raw Data

Use this if you only want to regenerate rankings, available-only tables, and plots from the already saved raw data.

```bash
python src/google_trends_marketing/run_trends_versioned.py --run-label python_v1 --use-existing-raw
```

## Wait And Retry Missing Terms In Small Chunks

Use these later when you want to try filling in only the missing terms without overwhelming Google Trends.

### First chunk of 3 pending terms

```bash
python src/google_trends_marketing/run_trends_versioned.py --run-label python_v1 --resume-existing-raw --limit 3 --continue-on-error --sleep 12
```

### Second chunk of 3 pending terms

```bash
python src/google_trends_marketing/run_trends_versioned.py --run-label python_v1 --resume-existing-raw --offset 3 --limit 3 --continue-on-error --sleep 12
```

### Third chunk of 3 pending terms

```bash
python src/google_trends_marketing/run_trends_versioned.py --run-label python_v1 --resume-existing-raw --offset 6 --limit 3 --continue-on-error --sleep 12
```

### More conservative single-term retry

If Google is still throttling requests, try one term at a time with a larger sleep:

```bash
python src/google_trends_marketing/run_trends_versioned.py --run-label python_v1 --resume-existing-raw --limit 1 --continue-on-error --sleep 60
```

## Files To Check After Each Retry

- Main ranking:
  - `data/processed/python_v1/keyword_opportunity_ranking.csv`
- Non-benchmark ranking:
  - `data/processed/python_v1/keyword_opportunity_ranking_non_benchmarks.csv`
- Benchmark comparison:
  - `data/processed/python_v1/benchmark_comparison.csv`
- Clean monthly file with only fetched columns:
  - `data/processed/python_v1/trends_monthly_available_only.csv`
- Failed term log:
  - `data/raw/trends/python_v1/trends_failed_terms.csv`

## Open The Best Current Plots

```bash
open "outputs/plots/google_trends_marketing/python_v1/top_keyword_opportunities.png"
open "outputs/plots/google_trends_marketing/python_v1/avila_vs_top_trends.png"
open "outputs/plots/google_trends_marketing/python_v1/avila_vs_benchmarks.png"
```

## If You Want A New Version Instead Of Updating `python_v1`

```bash
python src/google_trends_marketing/run_trends_versioned.py --run-label python_v2 --resume-existing-raw --limit 3 --continue-on-error --sleep 12
```

## Worldwide Note

- `python_v1` is not worldwide.
- If you want a separate worldwide run, use a new label so it does not mix with the California-focused data:

```bash
python src/google_trends_marketing/run_trends_versioned.py --run-label python_world_v1 --geo "" --resume-existing-raw --limit 1 --continue-on-error --sleep 60
```
