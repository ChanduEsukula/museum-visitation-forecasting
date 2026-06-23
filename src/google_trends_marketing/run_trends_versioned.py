from __future__ import annotations

import argparse
import json
import subprocess
import sys
import shutil
from pathlib import Path


def run(cmd: list[str], cwd: Path) -> None:
    print('Running:', ' '.join(cmd))
    subprocess.run(cmd, cwd=cwd, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description='Run the trends pipeline into versioned output folders.')
    parser.add_argument('--run-label', default='python_v1', help='Version label, e.g. python_v1')
    parser.add_argument('--timeframe', default='2014-01-01 2025-12-31')
    parser.add_argument('--geo', default='US-CA')
    parser.add_argument('--sleep', type=float, default=6.0)
    parser.add_argument('--use-existing-raw', action='store_true')
    parser.add_argument('--resume-existing-raw', action='store_true')
    parser.add_argument('--offset', type=int, default=0)
    parser.add_argument('--limit', type=int, default=0)
    parser.add_argument('--continue-on-error', action='store_true')
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[2]
    py = sys.executable

    processed_dir = root / 'data' / 'processed' / args.run_label
    raw_dir = root / 'data' / 'raw' / 'trends' / args.run_label
    plots_dir = root / 'outputs' / 'plots' / 'google_trends_marketing' / args.run_label

    processed_dir.mkdir(parents=True, exist_ok=True)
    raw_dir.mkdir(parents=True, exist_ok=True)
    plots_dir.mkdir(parents=True, exist_ok=True)

    versioned_raw = raw_dir / 'trends_weekly_long.csv'
    default_raw = root / 'data' / 'raw' / 'trends' / 'trends_weekly_long.csv'
    if args.use_existing_raw and not versioned_raw.exists() and default_raw.exists():
        shutil.copy2(default_raw, versioned_raw)

    fetch_cmd = [
        py,
        'src/google_trends_marketing/fetch_google_trends.py',
        '--timeframe', args.timeframe,
        '--geo', args.geo,
        '--sleep', str(args.sleep),
        '--out-raw', str(versioned_raw),
        '--out-monthly-long', str(processed_dir / 'trends_monthly_long.csv'),
        '--out-monthly-wide', str(processed_dir / 'trends_monthly.csv'),
        '--out-presentation', str(processed_dir / 'trends_monthly_dataset.csv'),
        '--meta-json', str(raw_dir / 'trends_fetch_meta.json'),
        '--failed-terms-csv', str(raw_dir / 'trends_failed_terms.csv'),
    ]
    if args.use_existing_raw:
        fetch_cmd.append('--use-existing-raw')
    if args.resume_existing_raw:
        fetch_cmd.append('--resume-existing-raw')
    if args.offset:
        fetch_cmd.extend(['--offset', str(args.offset)])
    if args.limit:
        fetch_cmd.extend(['--limit', str(args.limit)])
    if args.continue_on_error:
        fetch_cmd.append('--continue-on-error')
    run(fetch_cmd, root)

    ranking_cmd = [
        py,
        'src/google_trends_marketing/rank_trends_keywords.py',
        '--monthly-long', str(processed_dir / 'trends_monthly_long.csv'),
        '--keywords-csv', 'data/raw/trends/keywords.csv',
        '--out-csv', str(processed_dir / 'keyword_opportunity_ranking.csv'),
        '--out-non-benchmark-csv', str(processed_dir / 'keyword_opportunity_ranking_non_benchmarks.csv'),
        '--out-benchmark-comparison-csv', str(processed_dir / 'benchmark_comparison.csv'),
    ]
    run(ranking_cmd, root)

    summary_cmd = [
        py,
        'src/google_trends_marketing/summarize_trends_insights.py',
        '--ranking-csv', str(processed_dir / 'keyword_opportunity_ranking.csv'),
        '--monthly-csv', str(processed_dir / 'trends_monthly.csv'),
        '--monthly-long-csv', str(processed_dir / 'trends_monthly_long.csv'),
        '--museum-csv', '../museum-visitors.csv',
        '--plots-dir', str(plots_dir),
        '--out-available-csv', str(processed_dir / 'trends_monthly_available_only.csv'),
    ]
    run(summary_cmd, root)

    manifest = {
        'run_label': args.run_label,
        'timeframe': args.timeframe,
        'geo': args.geo,
        'processed_dir': str(processed_dir.relative_to(root)),
        'raw_dir': str(raw_dir.relative_to(root)),
        'plots_dir': str(plots_dir.relative_to(root)),
        'notes': [
            'Google Trends values are normalized 0-100 within the selected timeframe and geo.',
            'Peak trend values are peaks within this run window, not all-time search volume.',
            'Use trends_monthly_available_only.csv when you want no empty columns.',
            'Use keyword_opportunity_ranking_non_benchmarks.csv when you want rankings without competitors.',
        ],
    }
    (processed_dir / 'run_manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    print('Wrote', processed_dir / 'run_manifest.json')


if __name__ == '__main__':
    main()
