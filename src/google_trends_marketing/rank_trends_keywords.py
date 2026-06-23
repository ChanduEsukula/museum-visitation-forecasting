from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def build_ranking(monthly_long_path: Path, keywords_path: Path) -> pd.DataFrame:
    keywords = pd.read_csv(keywords_path)
    monthly_long = pd.read_csv(monthly_long_path)

    if monthly_long.empty:
        out = keywords.copy()
        out['has_available_data'] = False
        out['months_with_data'] = 0
        out['nonzero_months'] = 0
        out['coverage_pct'] = 0.0
        out['active_month_pct'] = 0.0
        out['avg_trend'] = pd.NA
        out['recent_12m_avg'] = pd.NA
        out['peak_trend'] = pd.NA
        out['latest_month'] = pd.NA
        out['latest_value'] = pd.NA
        out['opportunity_score'] = pd.NA
        out['rank_overall'] = pd.NA
        return out

    monthly_long['month'] = pd.to_datetime(monthly_long['month'] + '-01', errors='coerce')
    monthly_long['value'] = pd.to_numeric(monthly_long['value'], errors='coerce')
    total_months = monthly_long['month'].dropna().dt.to_period('M').nunique()

    rows = []
    for term, group in monthly_long.groupby('term', dropna=False):
        g = group.dropna(subset=['month']).sort_values('month').copy()
        if g.empty:
            continue
        values = g['value']
        nonzero = values.fillna(0).gt(0)
        recent = g.tail(12)
        months_with_data = int(values.notna().sum())
        nonzero_months = int(nonzero.sum())
        coverage_pct = round((months_with_data / total_months) * 100, 2) if total_months else 0.0
        active_month_pct = round((nonzero_months / months_with_data) * 100, 2) if months_with_data else 0.0
        avg_trend = round(float(values.mean()), 2) if months_with_data else pd.NA
        recent_12m_avg = round(float(recent['value'].mean()), 2) if not recent.empty else pd.NA
        peak_trend = round(float(values.max()), 2) if months_with_data else pd.NA
        latest_month = g['month'].iloc[-1].strftime('%Y-%m')
        latest_value = round(float(g['value'].iloc[-1]), 2) if pd.notna(g['value'].iloc[-1]) else pd.NA
        opportunity_score = round(
            0.45 * (recent_12m_avg if pd.notna(recent_12m_avg) else 0)
            + 0.25 * (avg_trend if pd.notna(avg_trend) else 0)
            + 0.15 * (peak_trend if pd.notna(peak_trend) else 0)
            + 0.10 * active_month_pct
            + 0.05 * coverage_pct,
            2,
        )
        rows.append({
            'term': term,
            'has_available_data': True,
            'months_with_data': months_with_data,
            'nonzero_months': nonzero_months,
            'coverage_pct': coverage_pct,
            'active_month_pct': active_month_pct,
            'avg_trend': avg_trend,
            'recent_12m_avg': recent_12m_avg,
            'peak_trend': peak_trend,
            'latest_month': latest_month,
            'latest_value': latest_value,
            'opportunity_score': opportunity_score,
        })

    ranked = pd.DataFrame(rows)
    out = keywords.merge(ranked, on='term', how='left')
    out['has_available_data'] = out['has_available_data'].fillna(False)
    out = out.sort_values(['has_available_data', 'opportunity_score', 'avg_trend'], ascending=[False, False, False]).reset_index(drop=True)
    available_mask = out['has_available_data']
    out.loc[available_mask, 'rank_overall'] = range(1, int(available_mask.sum()) + 1)
    return out


def build_benchmark_comparison(ranking: pd.DataFrame) -> pd.DataFrame:
    subset = ranking[ranking['term'].isin([
        'Avila Adobe',
        'Getty Museum',
        'La Brea Tar Pits',
        'Griffith Observatory',
    ])].copy()
    keep = [
        'term',
        'lane',
        'theme',
        'avg_trend',
        'recent_12m_avg',
        'peak_trend',
        'latest_month',
        'latest_value',
        'opportunity_score',
        'rank_overall',
    ]
    present = [c for c in keep if c in subset.columns]
    return subset[present].sort_values('avg_trend', ascending=False, na_position='last').reset_index(drop=True)


def main() -> None:
    parser = argparse.ArgumentParser(description='Rank Google Trends keywords from available monthly outputs.')
    parser.add_argument('--monthly-long', type=Path, default=Path('data/processed/avila_marketing_trends_monthly_long.csv'))
    parser.add_argument('--keywords-csv', type=Path, default=Path('data/raw/trends/keywords.csv'))
    parser.add_argument('--out-csv', type=Path, default=Path('data/processed/avila_keyword_opportunity_ranking.csv'))
    parser.add_argument(
        '--out-non-benchmark-csv',
        type=Path,
        default=Path('data/processed/avila_keyword_opportunity_ranking_non_benchmarks.csv'),
    )
    parser.add_argument(
        '--out-benchmark-comparison-csv',
        type=Path,
        default=Path('data/processed/avila_benchmark_comparison.csv'),
    )
    args = parser.parse_args()

    ranking = build_ranking(args.monthly_long, args.keywords_csv)
    args.out_csv.parent.mkdir(parents=True, exist_ok=True)
    ranking.to_csv(args.out_csv, index=False)
    non_benchmark = ranking[ranking['lane'] != 'benchmark'].copy()
    non_benchmark.to_csv(args.out_non_benchmark_csv, index=False)
    benchmark = build_benchmark_comparison(ranking)
    benchmark.to_csv(args.out_benchmark_comparison_csv, index=False)
    print(f'Wrote {args.out_csv}')
    print(f'Wrote {args.out_non_benchmark_csv}')
    print(f'Wrote {args.out_benchmark_comparison_csv}')


if __name__ == '__main__':
    main()
