# LinkedIn Post Assets

## Polished LinkedIn Post

I cleaned up a small applied machine learning project on museum visitation forecasting and turned it into a portfolio-ready case study.

The project estimates monthly visitation for Avila Adobe, a historic site in Los Angeles, using public attendance history, weather data, calendar/seasonality features, lagged visitor counts, and Google Trends search-interest signals.

What made the project interesting was the feature story. The best committed model was LASSO-LARS, with RMSE around 2,982 visitors and R2 around 0.783 on the holdout set. More importantly, the model showed that lagged visitation and seasonality carried most of the signal. Google Trends added useful demand context, but it needed careful interpretation because search interest is relative and not causal.

This is not a production forecasting system. It is a focused student/applied ML portfolio project with a small dataset, a 13-month holdout, and clear limitations. But it was a strong exercise in building an end-to-end workflow: data cleaning, feature engineering, model comparison, visualization, and honest evaluation.

Main takeaway: small data projects can still be valuable when the methodology is clear, the baselines are respected, and the limitations are stated plainly.

## Shorter LinkedIn Post

I polished a student/applied ML project into a portfolio case study: monthly museum visitation forecasting for Avila Adobe in Los Angeles.

The project combines attendance history, weather, calendar features, lagged visitation, and Google Trends search-interest signals. The best committed model was LASSO-LARS, with RMSE around 2,982 visitors and R2 around 0.783 on the holdout set.

The biggest lesson: historical attendance and seasonality mattered more than flashy external features. Google Trends was useful for public-interest context, but not something to interpret causally.

Small dataset, honest scope, end-to-end workflow.

## Technical LinkedIn Post

I turned a small museum visitation dataset into an end-to-end applied ML forecasting project.

Scope:

- Target: monthly Avila Adobe visitation
- Features: weather, calendar signals, Google Trends, lag-1, lag-12, rolling visitor average
- Models: Linear Regression, LASSO, LASSO-LARS, Random Forest, Gradient Boosting
- Metrics: RMSE, MAE, R2
- Evaluation: chronological holdout, not random shuffling

Best committed model:

- LASSO-LARS
- RMSE: 2,982.044
- MAE: 2,259.141
- R2: 0.783

What I would improve next:

- add rolling-origin backtesting
- test lagged external features for true ahead-of-month forecasting
- add prediction intervals
- compare against naive seasonal baselines
- expand beyond one museum

The project is intentionally modest, but it demonstrates the kind of applied ML judgment that matters in real work: data quality, leakage awareness, feature interpretation, and honest evaluation.

## GitHub Repo Description

Short-horizon museum visitation forecasting using public attendance, weather, calendar, lag, and Google Trends search-interest signals.

## GitHub Topics / Tags

- data-science
- machine-learning
- forecasting
- time-series
- scikit-learn
- feature-engineering
- google-trends
- portfolio-project
- python
- museum-analytics
- applied-ml
- data-visualization

## Resume Bullets

- Built an applied ML workflow to estimate monthly museum visitation using attendance history, weather, calendar, lag, and Google Trends features.
- Engineered lag-1, lag-12, rolling average, seasonality, holiday, and search-interest predictors for a small monthly forecasting dataset.
- Evaluated Linear Regression, LASSO, LASSO-LARS, Random Forest, and Gradient Boosting models using RMSE, MAE, and R2 on a chronological holdout set.
- Identified regularized linear models as strongest for the committed feature set, with LASSO-LARS reaching RMSE 2,982 and R2 0.783.
- Created portfolio-ready documentation and visuals explaining model performance, feature importance, Google Trends caveats, and project limitations.

## Interview Talking Points

- Why a chronological split is more appropriate than random splitting for monthly forecasting.
- Why lagged attendance and seasonality dominate in small visitation datasets.
- Why Google Trends is useful as public-interest context but should not be interpreted causally.
- How correlated features hurt plain linear regression and why regularization helps.
- What I would do next: rolling-origin validation, naive baselines, lagged external signals, prediction intervals, and multi-site generalization.

## Honest Limitations

- The cleaned portfolio framing uses only 62 final modeling rows after strict filtering and lag creation.
- The holdout period is only 13 months, so results should be treated as directional.
- The project focuses on one site, Avila Adobe, so it is not automatically generalizable.
- Same-month weather and Google Trends features make the current framing closer to nowcasting than true future forecasting.
- The current committed workflow does not yet include rolling-origin backtesting.
- Forecasts do not include prediction intervals or uncertainty bands.
- Google Trends values are relative 0-100 indices and should not be treated as direct search volume or causal marketing impact.

## Suggested Screenshots / Images

- `outputs/plots/lasso_actual_vs_predicted.png`
- `outputs/plots/lasso_top_predictors_plot.png`
- `outputs/plots/rf_feature_importance.png`
- `outputs/presentation/monthly_visitors.png`
- `outputs/plots/google_trends_marketing/google-trends-marketing-v6/top_keyword_opportunities.png`
- `outputs/plots/google_trends_marketing/google-trends-marketing-v6/avila_vs_top_trends_scaled.png`

Best LinkedIn carousel order:

1. Monthly visitor trend
2. Model comparison or actual-vs-predicted plot
3. Top predictors or feature importance
4. Google Trends keyword opportunity chart
5. Final slide with limitations and future work

## What I Learned

- A clean project story matters as much as model choice for portfolio work.
- Time-aware validation is essential for forecasting-style projects.
- Small datasets make regularization, baselines, and humility more important.
- External signals can add useful context without being strong causal predictors.
- Results are more credible when limitations are visible instead of hidden.
