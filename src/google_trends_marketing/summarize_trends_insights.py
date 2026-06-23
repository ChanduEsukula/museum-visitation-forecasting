from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import re


def min_max_scale(series: pd.Series) -> pd.Series:
    s = pd.to_numeric(series, errors='coerce')
    if s.dropna().empty:
        return s
    mn = s.min()
    mx = s.max()
    if pd.isna(mn) or pd.isna(mx) or mx == mn:
        return pd.Series([0.0] * len(s), index=s.index)
    return (s - mn) / (mx - mn)


def slugify_term(term: str) -> str:
    s = term.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    return f"trends_{s}"


def load_avila_visitors(museum_csv: Path) -> pd.DataFrame:
    df = pd.read_csv(museum_csv)
    month_col = 'Month' if 'Month' in df.columns else df.columns[0]
    avila_col = 'Avila Adobe'
    if avila_col not in df.columns:
        raise SystemExit(f'Missing expected column {avila_col!r} in {museum_csv}')
    out = df[[month_col, avila_col]].copy()
    out.columns = ['month_raw', 'avila_visitors']
    out['month'] = pd.to_datetime(out['month_raw'], errors='coerce').dt.to_period('M').astype(str)
    out['avila_visitors'] = pd.to_numeric(out['avila_visitors'], errors='coerce')
    return out[['month', 'avila_visitors']]


def print_section(title: str) -> None:
    print(f"\n{title}")
    print('-' * len(title))


def main() -> None:
    parser = argparse.ArgumentParser(description='Print Trends insights and save charts.')
    parser.add_argument('--ranking-csv', type=Path, default=Path('data/processed/avila_keyword_opportunity_ranking.csv'))
    parser.add_argument('--monthly-csv', type=Path, default=Path('data/processed/avila_marketing_trends_monthly.csv'))
    parser.add_argument('--monthly-long-csv', type=Path, default=Path('data/processed/avila_marketing_trends_monthly_long.csv'))
    parser.add_argument('--museum-csv', type=Path, default=Path('../museum-visitors.csv'))
    parser.add_argument('--plots-dir', type=Path, default=Path('outputs/plots/google_trends_marketing'))
    parser.add_argument('--out-available-csv', type=Path, default=Path('data/processed/avila_marketing_trends_monthly_available_only.csv'))
    args = parser.parse_args()

    ranking = pd.read_csv(args.ranking_csv)
    monthly = pd.read_csv(args.monthly_csv)
    monthly_long = pd.read_csv(args.monthly_long_csv)
    museum = load_avila_visitors(args.museum_csv)
    args.plots_dir.mkdir(parents=True, exist_ok=True)

    available = ranking[ranking['has_available_data'] == True].copy()
    top_terms = available.head(10).copy()
    available_terms = available['term'].dropna().tolist()
    available_cols = ['month'] + [slugify_term(term) for term in available_terms]
    available_cols = [c for c in available_cols if c in monthly.columns]
    monthly[available_cols].to_csv(args.out_available_csv, index=False)

    print_section('Top Ranked Available Terms')
    print(top_terms[['rank_overall', 'term', 'theme', 'avg_trend', 'recent_12m_avg', 'opportunity_score']].to_string(index=False))

    theme_summary = (
        available.groupby('theme', dropna=False)
        .agg(
            keywords=('term', 'count'),
            avg_opportunity_score=('opportunity_score', 'mean'),
            avg_trend=('avg_trend', 'mean'),
        )
        .sort_values('avg_opportunity_score', ascending=False)
        .round(2)
        .reset_index()
    )
    print_section('Theme Summary')
    print(theme_summary.to_string(index=False))

    unfetched = ranking[ranking['has_available_data'] != True][['term', 'theme', 'lane']].copy()
    if not unfetched.empty:
        print_section('Terms Still Waiting On Live Fetch')
        print(unfetched.to_string(index=False))

    print_section('Visitor Alignment Snapshot')
    merged = monthly.merge(museum, on='month', how='left')
    candidate_cols = [
        'trends_avila_adobe',
        'trends_olvera_street',
        'trends_los_angeles_history',
        'trends_los_angeles_museums',
        'trends_things_to_do_in_los_angeles',
        'trends_family_activities_los_angeles',
    ]
    rows = []
    for col in candidate_cols:
        if col not in merged.columns:
            continue
        corr = merged[['avila_visitors', col]].corr(numeric_only=True).iloc[0, 1]
        rows.append({'column': col, 'corr_with_avila_visitors': None if pd.isna(corr) else round(float(corr), 3)})
    corr_df = pd.DataFrame(rows).sort_values('corr_with_avila_visitors', ascending=False, na_position='last')
    print(corr_df.to_string(index=False))

    plt.style.use('seaborn-v0_8-whitegrid')

    # Chart 1: top opportunity scores
    fig, ax = plt.subplots(figsize=(12, 6))
    chart = top_terms.sort_values('opportunity_score')
    ax.barh(chart['term'], chart['opportunity_score'], color='#7a2e2e')
    ax.set_title('Top Available Google Trends Opportunities for Avila Adobe')
    ax.set_xlabel('Opportunity score')
    fig.tight_layout()
    fig.savefig(args.plots_dir / 'top_keyword_opportunities.png', dpi=160)
    plt.close(fig)

    # Chart 2: normalized line comparison with visitors
    line_cols = [
        ('Avila visitors', 'avila_visitors'),
        ('Olvera Street', 'trends_olvera_street'),
        ('Los Angeles history', 'trends_los_angeles_history'),
        ('Things to do in Los Angeles', 'trends_things_to_do_in_los_angeles'),
    ]
    fig, ax = plt.subplots(figsize=(13, 6))
    x = pd.to_datetime(merged['month'] + '-01', errors='coerce')
    for label, col in line_cols:
        if col not in merged.columns:
            continue
        ax.plot(x, min_max_scale(merged[col]), label=label, linewidth=2)
    ax.set_title('Normalized Visitor vs Search-Interest Trends')
    ax.set_ylabel('Min-max scaled value')
    ax.legend()
    fig.tight_layout()
    fig.savefig(args.plots_dir / 'avila_vs_top_trends.png', dpi=160)
    plt.close(fig)

    # Chart 3: theme opportunity summary
    fig, ax = plt.subplots(figsize=(11, 6))
    theme_chart = theme_summary.sort_values('avg_opportunity_score')
    ax.barh(theme_chart['theme'], theme_chart['avg_opportunity_score'], color='#355c7d')
    ax.set_title('Average Opportunity Score by Theme')
    ax.set_xlabel('Average opportunity score')
    fig.tight_layout()
    fig.savefig(args.plots_dir / 'theme_opportunity_scores.png', dpi=160)
    plt.close(fig)

    # Chart 4: all available terms over time as scatter
    if not monthly_long.empty:
        scatter = monthly_long.copy()
        scatter['month'] = pd.to_datetime(scatter['month'] + '-01', errors='coerce')
        scatter = scatter[scatter['term'].isin(available_terms)]
        scatter = scatter[scatter['value'].fillna(0) > 0]
        if not scatter.empty:
            term_order = available.sort_values('opportunity_score', ascending=False)['term'].tolist()
            y_map = {term: i for i, term in enumerate(term_order)}
            scatter['y'] = scatter['term'].map(y_map)
            fig, ax = plt.subplots(figsize=(15, 8))
            points = ax.scatter(
                scatter['month'],
                scatter['y'],
                s=scatter['value'] * 4,
                c=scatter['value'],
                cmap='viridis',
                alpha=0.75,
            )
            ax.set_yticks(range(len(term_order)))
            ax.set_yticklabels(term_order)
            ax.set_title('Available Google Trends Terms Over Time') 
            ax.set_xlabel('Month')
            ax.set_ylabel('Search term')
            fig.colorbar(points, ax=ax, label='Trend value (0-100)')
            fig.tight_layout()
            fig.savefig(args.plots_dir / 'all_terms_scatter_over_time.png', dpi=160)
            plt.close(fig)

    # Chart 5: Avila vs benchmark terms
    benchmark_cols = [
        ('Avila Adobe', 'trends_avila_adobe'),
        ('Getty Museum', 'trends_getty_museum'),
        ('La Brea Tar Pits', 'trends_la_brea_tar_pits'),
        ('Griffith Observatory', 'trends_griffith_observatory'),
    ]
    fig, ax = plt.subplots(figsize=(13, 6))
    for label, col in benchmark_cols:
        if col not in merged.columns:
            continue
        ax.plot(x, min_max_scale(merged[col]), label=label, linewidth=2)
    ax.set_title('Normalized Avila Search vs Benchmark Searches')
    ax.set_ylabel('Min-max scaled value')
    ax.legend()
    fig.tight_layout()
    fig.savefig(args.plots_dir / 'avila_vs_benchmarks.png', dpi=160)
    plt.close(fig)

    print_section('Saved Plots')
    for name in [
        'top_keyword_opportunities.png',
        'avila_vs_top_trends.png',
        'theme_opportunity_scores.png',
        'all_terms_scatter_over_time.png',
        'avila_vs_benchmarks.png',
    ]:
        print(args.plots_dir / name)
    print(args.out_available_csv)


if __name__ == '__main__':
    main()
