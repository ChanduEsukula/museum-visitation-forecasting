from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

import pandas as pd


def slugify_term(term: str) -> str:
    s = term.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    return f"trends_{s}"


def weekly_to_monthly_mean(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=['month', 'value'])
    out = df.copy()
    out['date'] = pd.to_datetime(out['date'], errors='coerce')
    out['value'] = pd.to_numeric(out['value'], errors='coerce')
    out = out.dropna(subset=['date', 'value']).sort_values('date')
    if out.empty:
        return pd.DataFrame(columns=['month', 'value'])
    monthly = out.set_index('date')['value'].resample('ME').mean().reset_index()
    monthly.columns = ['month_end', 'value']
    monthly['month'] = monthly['month_end'].dt.to_period('M').astype(str)
    return monthly[['month', 'value']]


def to_presentation_dataset(monthly_term_wide: pd.DataFrame) -> pd.DataFrame:
    if monthly_term_wide.empty:
        return pd.DataFrame(columns=['Month'])
    wide = monthly_term_wide.copy().rename(columns={'month': 'Month'})
    wide['Month'] = pd.to_datetime(wide['Month'] + '-01').dt.strftime('%Y-%m-%dT00:00:00.000')
    cols = [c for c in wide.columns if c != 'Month']
    return wide[['Month', *cols]]


def parse_term_and_geo(col_name: str) -> tuple[str, str]:
    col_name = str(col_name).strip()
    match = re.match(r'^(.*?)(?:\s*:\s*\((.*?)\))?$', col_name)
    if not match:
        return col_name, ''
    term = match.group(1).strip()
    geo = (match.group(2) or '').strip()
    return term, geo


def parse_export_csv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, skiprows=1)
    if df.empty or len(df.columns) < 2:
        raise ValueError(f'Unexpected Google Trends export format: {path}')
    date_col = df.columns[0]
    value_col = df.columns[1]
    term, geo = parse_term_and_geo(value_col)
    out = df[[date_col, value_col]].copy()
    out.columns = ['date', 'value']
    out['value'] = out['value'].replace('<1', '0')
    out['date'] = pd.to_datetime(out['date'], errors='coerce')
    out['value'] = pd.to_numeric(out['value'], errors='coerce')
    out = out.dropna(subset=['date', 'value'])
    out['term'] = term
    out['geo_label'] = geo
    return out


def run(cmd: list[str], cwd: Path) -> None:
    print('Running:', ' '.join(cmd))
    subprocess.run(cmd, cwd=cwd, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description='Import manually exported Google Trends CSVs into a versioned run folder.')
    parser.add_argument('--exports-dir', type=Path, required=True, help='Directory containing Google Trends CSV exports (one term per file).')
    parser.add_argument('--run-label', default='python_manual_v1')
    parser.add_argument('--keywords-csv', type=Path, default=Path('data/raw/trends/keywords.csv'))
    parser.add_argument('--museum-csv', type=Path, default=Path('../museum-visitors.csv'))
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[2]
    py = sys.executable
    exports_dir = args.exports_dir if args.exports_dir.is_absolute() else (root / args.exports_dir)
    if not exports_dir.exists():
        raise SystemExit(f'Exports directory not found: {exports_dir}')

    processed_dir = root / 'data' / 'processed' / args.run_label
    raw_dir = root / 'data' / 'raw' / 'trends' / args.run_label
    plots_dir = root / 'outputs' / 'plots' / 'google_trends_marketing' / args.run_label
    processed_dir.mkdir(parents=True, exist_ok=True)
    raw_dir.mkdir(parents=True, exist_ok=True)
    plots_dir.mkdir(parents=True, exist_ok=True)

    keywords = pd.read_csv(root / args.keywords_csv)
    files = sorted(exports_dir.glob('*.csv'))
    if not files:
        raise SystemExit(f'No CSV exports found in {exports_dir}')

    raw_parts = []
    for file in files:
        raw_parts.append(parse_export_csv(file))
    raw_long = pd.concat(raw_parts, ignore_index=True) if raw_parts else pd.DataFrame()
    raw_long = raw_long.merge(keywords[['term', 'lane', 'theme', 'notes']], on='term', how='left')
    raw_long['source'] = 'Manual Google Trends export'
    raw_long.to_csv(raw_dir / 'trends_weekly_long.csv', index=False)

    monthly_parts = []
    for term, group in raw_long.groupby('term', dropna=False):
        monthly = weekly_to_monthly_mean(group[['date', 'value']])
        monthly['term'] = term
        meta = keywords[keywords['term'] == term]
        if not meta.empty:
            row = meta.iloc[0]
            monthly['lane'] = row['lane']
            monthly['theme'] = row['theme']
            monthly['notes'] = row.get('notes', '')
        else:
            monthly['lane'] = pd.NA
            monthly['theme'] = pd.NA
            monthly['notes'] = pd.NA
        geo_label = group['geo_label'].dropna().astype(str)
        monthly['geo'] = geo_label.iloc[0] if not geo_label.empty else ''
        monthly['source'] = 'Manual Google Trends export'
        monthly_parts.append(monthly)

    monthly_long = pd.concat(monthly_parts, ignore_index=True) if monthly_parts else pd.DataFrame()
    monthly_long.to_csv(processed_dir / 'trends_monthly_long.csv', index=False)

    if monthly_long.empty:
        wide = pd.DataFrame(columns=['month'])
    else:
        wide = monthly_long.pivot_table(index='month', columns='term', values='value', aggfunc='mean').reset_index()
    cols = ['month'] + [c for c in wide.columns if c != 'month']
    wide = wide[cols]
    wide_slug = wide.rename(columns={c: slugify_term(c) for c in wide.columns if c != 'month'})
    wide_slug.to_csv(processed_dir / 'trends_monthly.csv', index=False)
    presentation = to_presentation_dataset(wide)
    presentation.to_csv(processed_dir / 'trends_monthly_dataset.csv', index=False)

    run([
        py,
        'src/google_trends_marketing/rank_trends_keywords.py',
        '--monthly-long', str(processed_dir / 'trends_monthly_long.csv'),
        '--keywords-csv', 'data/raw/trends/keywords.csv',
        '--out-csv', str(processed_dir / 'keyword_opportunity_ranking.csv'),
        '--out-non-benchmark-csv', str(processed_dir / 'keyword_opportunity_ranking_non_benchmarks.csv'),
        '--out-benchmark-comparison-csv', str(processed_dir / 'benchmark_comparison.csv'),
    ], root)

    run([
        py,
        'src/google_trends_marketing/summarize_trends_insights.py',
        '--ranking-csv', str(processed_dir / 'keyword_opportunity_ranking.csv'),
        '--monthly-csv', str(processed_dir / 'trends_monthly.csv'),
        '--monthly-long-csv', str(processed_dir / 'trends_monthly_long.csv'),
        '--museum-csv', str(args.museum_csv),
        '--plots-dir', str(plots_dir),
        '--out-available-csv', str(processed_dir / 'trends_monthly_available_only.csv'),
    ], root)

    print(f'Imported {len(files)} export files into {processed_dir}')


if __name__ == '__main__':
    main()
