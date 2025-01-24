# Average Treatment Effect (ATE)

ATE measures how much impact a given intervention policy has relative to some baseline scenario. Large ATE means large impact.

Here is how you could calculate ATE:

```python
def average_treatment_effect(df_baseline: pd.DataFrame, df_treatment: pd.DataFrame, outcome: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    
    num_samples_0 = len(df_baseline['sample_id'].unique())
    x0 = df_baseline[['timepoint_unknown', outcome]].groupby(['timepoint_unknown'])
    x0_mean = x0.mean()
    x0_mean_err = x0.std() / np.sqrt(num_samples_0)
    
    num_samples_1 = len(df_treatment['sample_id'].unique())
    x1 = df_treatment[['timepoint_unknown', outcome]].groupby(['timepoint_unknown'])
    x1_mean = x1.mean()
    x1_mean_err = x1.std() / np.sqrt(num_samples_1)

    ate = (x1_mean - x0_mean).reset_index()
    ate_err = (np.sqrt(x0_mean_err ** 2.0 + x1_mean_err ** 2.0)).reset_index()

    return (ate, ate_err)
```

Here is how you might plot the ATE:

```python
import matplotlib.pyplot as plt

fig, axes = plt.subplots(1, 2, figsize = (12, 6))
fig.suptitle = 'Average Treatment Effect'

for outcome in ('S_state', 'I_state', 'R_state'):
    for ax, df_treatment in zip(axes, (d2, d3)):
        ate, ate_err = average_treatment_effect(d1, df_treatment, outcome)
        __ = ax.plot(ate['timepoint_unknown'], ate[outcome], label = outcome.split('_')[0])
        __ = ax.fill_between(ate['timepoint_unknown'], ate[outcome] - ate_err[outcome], ate[outcome] + ate_err[outcome], alpha = 0.5)

for ax in axes:
    __ = plt.setp(ax, xlabel = 'Timepoint (days)', ylabel = ('ATE (persons)'), ylim = (-900, 1200), xlim = (0, 100))
    __ = ax.legend()
    
__ = plt.setp(axes[0], title = 'Soft Policy vs. Baseline')
__ = plt.setp(axes[1], title = 'Hard Policy vs. Baseline')
```

# Weighted Interval Score (WIS)

WIS measures how good a given forecast is relative to some observations. Large WIS means bad forecast.

Here is how you might calculate WIS:

```python
# Interval Score
def interval_score(
    observations,
    alpha,
    q_dict=None,
    q_left=None,
    q_right=None,
    percent=False,
    check_consistency=True,
):
    """
    Compute interval scores (1) for an array of observations and predicted intervals.
    
    Either a dictionary with the respective (alpha/2) and (1-(alpha/2)) quantiles via q_dict needs to be
    specified or the quantiles need to be specified via q_left and q_right.
    
    Parameters
    ----------
    observations : array_like
        Ground truth observations.
    alpha : numeric
        Alpha level for (1-alpha) interval.
    q_dict : dict, optional
        Dictionary with predicted quantiles for all instances in `observations`.
    q_left : array_like, optional
        Predicted (alpha/2)-quantiles for all instances in `observations`.
    q_right : array_like, optional
        Predicted (1-(alpha/2))-quantiles for all instances in `observations`.
    percent: bool, optional
        If `True`, score is scaled by absolute value of observations to yield a percentage error. Default is `False`.
    check_consistency: bool, optional
        If `True`, quantiles in `q_dict` are checked for consistency. Default is `True`.
        
    Returns
    -------
    total : array_like
        Total interval scores.
    sharpness : array_like
        Sharpness component of interval scores.
    calibration : array_like
        Calibration component of interval scores.
        
    (1) Gneiting, T. and A. E. Raftery (2007). Strictly proper scoring rules, prediction, and estimation. Journal of the American Statistical Association 102(477), 359–378.    
    """

    if q_dict is None:
        if q_left is None or q_right is None:
            raise ValueError(
                "Either quantile dictionary or left and right quantile must be supplied."
            )
    else:
        if q_left is not None or q_right is not None:
            raise ValueError(
                "Either quantile dictionary OR left and right quantile must be supplied, not both."
            )
        q_left = q_dict.get(alpha / 2)
        if q_left is None:
            raise ValueError(f"Quantile dictionary does not include {alpha/2}-quantile")

        q_right = q_dict.get(1 - (alpha / 2))
        if q_right is None:
            raise ValueError(
                f"Quantile dictionary does not include {1-(alpha/2)}-quantile"
            )

    if check_consistency and np.any(q_left > q_right):
        raise ValueError("Left quantile must be smaller than right quantile.")

    sharpness = q_right - q_left
    calibration = (
        (
            np.clip(q_left - observations, a_min=0, a_max=None)
            + np.clip(observations - q_right, a_min=0, a_max=None)
        )
        * 2
        / alpha
    )
    if percent:
        sharpness = sharpness / np.abs(observations)
        calibration = calibration / np.abs(observations)
    total = sharpness + calibration
    return total, sharpness, calibration

# Weighted Interval Score
def weighted_interval_score(
    observations, alphas, q_dict, weights=None, percent=False, check_consistency=True
):
    """
    Compute weighted interval scores for an array of observations and a number of different predicted intervals.
    
    This function implements the WIS-score (2). A dictionary with the respective (alpha/2)
    and (1-(alpha/2)) quantiles for all alpha levels given in `alphas` needs to be specified.
    
    Parameters
    ----------
    observations : array_like
        Ground truth observations.
    alphas : iterable
        Alpha levels for (1-alpha) intervals.
    q_dict : dict
        Dictionary with predicted quantiles for all instances in `observations`.
    weights : iterable, optional
        Corresponding weights for each interval. If `None`, `weights` is set to `alphas`, yielding the WIS^alpha-score.
    percent: bool, optional
        If `True`, score is scaled by absolute value of observations to yield the double absolute percentage error. Default is `False`.
    check_consistency: bool, optional
        If `True`, quantiles in `q_dict` are checked for consistency. Default is `True`.
        
    Returns
    -------
    total : array_like
        Total weighted interval scores.
    sharpness : array_like
        Sharpness component of weighted interval scores.
    calibration : array_like
        Calibration component of weighted interval scores.
        
    (2) Bracher, J., Ray, E. L., Gneiting, T., & Reich, N. G. (2020). Evaluating epidemic forecasts in an interval format. arXiv preprint arXiv:2005.12881.
    """
    if weights is None:
        weights = np.array(alphas)/2

    def weigh_scores(tuple_in, weight):
        return tuple_in[0] * weight, tuple_in[1] * weight, tuple_in[2] * weight

    interval_scores = [
        i
        for i in zip(
            *[
                weigh_scores(
                    interval_score(
                        observations,
                        alpha,
                        q_dict=q_dict,
                        percent=percent,
                        check_consistency=check_consistency,
                    ),
                    weight,
                )
                for alpha, weight in zip(alphas, weights)
            ]
        )
    ]

    total = np.sum(np.vstack(interval_scores[0]), axis=0) / sum(weights)
    sharpness = np.sum(np.vstack(interval_scores[1]), axis=0) / sum(weights)
    calibration = np.sum(np.vstack(interval_scores[2]), axis=0) / sum(weights)

    return total, sharpness, calibration
```

Here is an example usage of WIS:

```python
# Forecast Hub required alpha quantiles
DEFAULT_ALPHA_QS = [
    0.01,
    0.025,
    0.05,
    0.1,
    0.15,
    0.2,
    0.25,
    0.3,
    0.35,
    0.4,
    0.45,
    0.5,
    0.55,
    0.6,
    0.65,
    0.7,
    0.75,
    0.8,
    0.85,
    0.9,
    0.95,
    0.975,
    0.99,
]

# Outcome of interest
outcome = 'I_state'

# Compute the quantiles of the observation (i.e. baseline)
observations = compute_quantile_dict(df_baseline, outcome = 'I_state', quantiles = DEFAULT_ALPHA_QS)[0.5]

# Compute the quantiles of the forecasts (i.e. simulation result)
q_dict = compute_quantile_dict(df_soft_policy, outcome = 'I_state', quantiles = DEFAULT_ALPHA_QS)

# Interval Score (IS) at alpha = 0.2
IS_total, IS_sharpness, IS_calibration = interval_score(
    observations, 
    alpha = 0.2,
    q_dict = q_dict, 
    percent = True
)

# Weighted Interval Score (WIS)
WIS_total, WIS_sharpness, WIS_calibration = weighted_interval_score_fast(
    observations,
    alphas = [0.02, 0.05, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9],
    weights = None, 
    q_dict = q_dict,
    percent = True
)
```

Here is how you might plot the `IS_total` and `WIS_total` scores (percentages):

```python
fig, ax in plt.subplots(1, 1, figsize = (8, 6))

x = df_baseline['timepoint_unknown'].unique()
y = IS_total
z = WIS_total

__ = ax.plot(x, y, label = 'IS_0.2')
__ = ax.plot(x, z, label = 'WIS')

__ = plt.setp(ax, xlabel = 'Timepoint (days)', ylabel = 'Score (%)', title = 'Interval Scores of Forecast Relative to Observations')
```

To compute values for the data table, simply take the mean of the arrays:

```python
outcome = 'S_state'
# ...
ate_mean = ate.mean() # ATE value for 'S' variable

WIS_total_mean = WIS_total.mean() # WIS value for 'S' variable
```