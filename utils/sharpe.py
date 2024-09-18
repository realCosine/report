import pandas as pd
import quantstats as qs
import numpy as np


def sharpe(returns, rf=0.0, periods=252, annualize=True, smart=False):
    """
    Calculate the Sharpe Ratio for a series of returns.

    returns : pd.Series or np.ndarray
        Series or array of periodic returns.
    """
    divisor = returns.std(ddof=1)

    if divisor == 0:
        return float("inf")

    if smart:
        divisor = divisor * qs.stats.autocorr_penalty(returns)
    res = returns.mean() / divisor
    if annualize:
        return res * np.sqrt(periods if periods else 1)
    return res


def prepare_df_for_sharpe(df):
    """
    Prepare a DataFrame for Sharpe Ratio calculation.
    Requires columns "LimitCreated" (datetime) and "ProfitPercent" (float), e.g. -1 (1% loss) in df.

    df : pd.DataFrame
        Input DataFrame containing at least the columns "LimitCreated" and "ProfitPercent".
    """
    df_copy = df.copy()
    df_copy["LimitCreated"] = pd.to_datetime(df_copy["LimitCreated"])
    df_copy["ProfitPercent"] = df_copy["ProfitPercent"] * 0.01
    df_copy = df_copy[["LimitCreated", "ProfitPercent"]]
    df_copy.set_index("LimitCreated", inplace=True)
    return df_copy["ProfitPercent"].fillna(0).sort_index()
