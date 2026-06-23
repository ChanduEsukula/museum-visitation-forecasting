# Museum Visitation Forecasting

A machine learning project that estimates monthly museum visitation using attendance history, weather, seasonality, calendar signals, and Google Trends search interest.

This repository is a cleaned personal portfolio version of a student applied ML project. It is intended to show an end-to-end data science workflow: data collection, feature engineering, modeling, evaluation, visualization, and honest documentation of limitations.

## Project Overview

The project focuses on monthly visitation at **Avila Adobe**, a historic site in Los Angeles. The goal is to estimate visitor volume using public, month-level signals that could plausibly help with staffing, programming, and marketing planning.

The workflow combines:

- historical museum attendance
- monthly Los Angeles weather aggregates
- calendar and seasonality indicators
- Google Trends search-interest signals
- lag and rolling visitor features
- regression models evaluated on a time-based holdout

Because some predictors use same-month weather and Google Trends values, the project is best described as **short-horizon forecasting / nowcasting**, not a production-grade future forecasting system.

## Why This Matters

Museums and historic sites need to plan around demand patterns. Even a small monthly forecast can help answer practical questions:

- Which months usually need more staffing or visitor support?
- How much does historical seasonality explain attendance?
- Do public-interest signals such as Google Trends add useful context?
- Which search themes could inform content, SEO, or campaign timing?

The most useful lesson from this project is not that one model "solves" visitation forecasting. It is that simple, interpretable features and baseline-aware evaluation can turn a messy student dataset into a clearer applied ML case study.

## Data Sources

| Source | Role in Project | Notes |
|---|---|---|
| Museum attendance | Target variable | Monthly Avila Adobe visitors from a public Los Angeles museum visitor dataset |
| Weather | Context features | Monthly temperature, precipitation, and wind aggregates |
| Calendar | Seasonality features | Month, quarter, holiday, school-year, break, and tourism-season indicators |
| Google Trends | Public-interest context | California-focused relative search-interest values for museum, tourism, and local-history terms |
| Lag features | Forecasting memory | Prior-month, prior-year, and rolling visitor signals |

Google Trends values are relative 0-100 indices, not raw search counts. They should be interpreted as search-interest context, not as proof of marketing causality.

## Feature Engineering

Feature groups include:

- `visitors_lag1`: previous month visitation
- `visitors_lag12`: same month in the prior year
- `rolling_mean_3`: trailing 3-month visitor average
- weather aggregates such as `avg_temp_F`, `total_precip_in`, and `avg_wind_mph`
- calendar flags such as winter/summer indicators, holiday season, school-year month, and break periods
- Google Trends keyword columns for local attractions, museums, history, family activities, and benchmark terms

The lag features are the most important modeling signal because museum visitation is strongly seasonal and autocorrelated.

## Modeling Approach

The checked-in modeling notebook uses a chronological train/test split and evaluates regression models with RMSE, MAE, and R2.

Models compared in the current committed result table:

- Linear Regression
- Cleaned Linear Regression
- LASSO
- LASSO-LARS
- Random Forest
- Gradient Boosting

The strongest committed model is **LASSO-LARS**, which performs similarly to LASSO and gives an interpretable regularized linear model for a small, correlated feature set.

## Results

Current committed model comparison:

| Model | RMSE | MAE | R2 |
|---|---:|---:|---:|
| LASSO-LARS | 2982.044 | 2259.141 | 0.783 |
| LASSO | 2986.711 | 2258.057 | 0.782 |
| Gradient Boosting | 5001.671 | 3340.323 | 0.389 |
| Random Forest | 5533.448 | 3604.140 | 0.252 |
| Linear Regression | 8769.045 | 6205.897 | -0.879 |
| Cleaned Linear Regression | 8769.045 | 6205.897 | -0.879 |

Interpretation:

- Regularized linear models performed best on this small, high-dimensional dataset.
- Plain linear regression struggled because the feature set contains correlated and redundant predictors.
- Lag and seasonality features carried more signal than weather alone.
- Google Trends is useful for demand context and keyword research, but should not be treated as causal evidence.

## Key Visuals

Recommended visuals to review:

- [LASSO actual vs predicted](outputs/plots/lasso_actual_vs_predicted.png)
- [LASSO top predictors](outputs/plots/lasso_top_predictors_plot.png)
- [Random Forest feature importance](outputs/plots/rf_feature_importance.png)
- [Monthly visitor trend](outputs/presentation/monthly_visitors.png)
- [Top Google Trends keyword opportunities](outputs/plots/google_trends_marketing/google-trends-marketing-v6/top_keyword_opportunities.png)
- [Avila visitors vs selected search-interest trends](outputs/plots/google_trends_marketing/google-trends-marketing-v6/avila_vs_top_trends_scaled.png)

## How To Run

Python 3.11+ is recommended.

```bash
git clone https://github.com/ChanduEsukula/museum-visitation-forecasting
cd museum-visitation-forecasting
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Notebook workflow:

1. `notebooks/01_museum_data.ipynb`
2. `notebooks/02_weather_data.ipynb`
3. `notebooks/03_google_trends.ipynb`
4. `notebooks/08_build_final_dataset.ipynb`
5. `notebooks/09_create_model_dataset.ipynb`
6. `notebooks/06_modeling.ipynb`

Google Trends live fetching is optional because cached processed outputs are included. If you want to rebuild the Trends lane from cached data:

```bash
python src/google_trends_marketing/run_trends_versioned.py --run-label python_v1 --use-existing-raw
```

Google Trends can rate-limit live API pulls. Use cached raw data where possible for reproducibility.

## Repository Structure

```text
museum-visitation-forecasting/
├── README.md
├── requirements.txt
├── data/
│   ├── raw/
│   └── processed/
├── notebooks/
├── src/
│   └── google_trends_marketing/
├── outputs/
│   ├── plots/
│   ├── presentation/
│   └── tables/
└── docs/
    ├── archive/
    ├── google_trends_marketing/
    └── linkedin_post_assets.md
```

## Limitations

- **Small dataset:** the cleaned portfolio framing uses 62 final modeling rows after strict filtering and lag creation; older intermediate notebook artifacts are retained for transparency.
- **Small holdout:** model results are based on a 13-month holdout, so performance should be treated as directional rather than definitive.
- **Single-site scope:** the project focuses on Avila Adobe and should not be generalized to all museums without additional testing.
- **Nowcasting caveat:** same-month weather and Google Trends signals make this closer to nowcasting than pure before-the-month forecasting.
- **No rolling-origin backtest yet:** the project does not yet evaluate repeated time-based splits across multiple forecast windows.
- **No prediction intervals:** forecasts do not yet include uncertainty bands.
- **Google Trends is contextual:** search-interest signals are relative and should be interpreted carefully, not causally.

## My Contribution / Attribution

This repository is a cleaned personal portfolio version of a student/team project. The original work began collaboratively, and this public version is organized to present the applied ML workflow I can honestly discuss: dataset assembly, feature engineering, forecasting methodology, model evaluation, visualization, and documentation.

Archived class-style materials, if present, are retained only as background artifacts and are not the main portfolio deliverable. The README and LinkedIn assets foreground the cleaned project narrative and avoid overstating ownership or production readiness.

## Project Context

This project started in an academic setting and has been polished into a portfolio case study. It is a small applied machine learning project, not a production forecasting platform.

## Future Improvements

- Add rolling-origin backtesting across several holdout windows.
- Compare against simple forecasting baselines such as lag-1 and lag-12 naive models.
- Test lagged weather and lagged Google Trends features for true ahead-of-month forecasting.
- Add prediction intervals or quantile-based uncertainty estimates.
- Expand to multiple museums or historic sites for better generalization.
- Add event calendars, school calendars, marketing campaigns, or operations data if available.
- Move the notebook modeling workflow into reusable scripts with automated checks.
