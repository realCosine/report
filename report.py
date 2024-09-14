import os
import json
import quantstats as qs
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from itertools import product

from src import load_config

config = load_config()

base_directory = config["common"]["base_directory"]
specific_directory = os.path.join(
    base_directory, config["common"]["specific_directory"]
)
output_directory = os.path.join(
    specific_directory, config["modules"]["report"]["output_directory_suffix"]
)
output_directory_specific = os.path.join(
    specific_directory,
    config["modules"]["report"]["output_directory_suffix_specific"],
)

os.makedirs(output_directory, exist_ok=True)
os.makedirs(output_directory_specific, exist_ok=True)

is_csv_file = os.path.join(
    specific_directory, config["common"]["output_files"]["is_csv_file"]
)
oos_csv_file = os.path.join(
    specific_directory, config["common"]["output_files"]["oos_csv_file"]
)

is_df = pd.read_csv(is_csv_file)
oos_df = pd.read_csv(oos_csv_file)

qs.extend_pandas()


def sharpe(returns, rf=0.0, periods=252, annualize=True, smart=False):
    divisor = returns.std(ddof=1)
    if smart:
        divisor = divisor * qs.stats.autocorr_penalty(returns)
    res = returns.mean() / divisor
    if annualize:
        return res * np.sqrt(periods if periods else 1)
    return res


def prepare_market_data(df):
    df["LimitCreated"] = pd.to_datetime(df["LimitCreated"])
    df["ProfitPercent"] = df["ProfitPercent"] * 0.01
    df = df[["LimitCreated", "ProfitPercent"]]
    df.set_index("LimitCreated", inplace=True)
    return df["ProfitPercent"].fillna(0).sort_index()


def generate_quantstats_reports(is_data, oos_data):
    combined_returns = None

    markets = is_df["Market"].unique()

    for market, lookback_period in product(markets, is_df["IS_QuarterCount"].unique()):
        market_output_directory = os.path.join(output_directory, market)
        os.makedirs(market_output_directory, exist_ok=True)

        is_market_data = is_df[
            (is_df["Market"] == market) & (is_df["IS_QuarterCount"] == lookback_period)
        ]
        oos_market_data = oos_df[
            (oos_df["Market"] == market)
            & (oos_df["IS_QuarterCount"] == lookback_period)
        ]

        is_returns = prepare_market_data(is_market_data).loc[
            ~prepare_market_data(is_market_data).index.duplicated(keep="first")
        ]
        oos_returns = prepare_market_data(oos_market_data)

        if not oos_returns.empty:
            switch_date = oos_returns.index[0]
            combined_returns = pd.concat(
                [is_returns[is_returns.index < switch_date], oos_returns]
            )

            oos_report = os.path.join(
                market_output_directory,
                f"{market}_{lookback_period}_oos_report.html",
            )
            qs.reports.html(oos_returns, output=oos_report)
        else:
            combined_returns = is_returns

        if not is_returns.empty:
            is_report = os.path.join(
                market_output_directory,
                f"{market}_{lookback_period}_is_report.html",
            )
            qs.reports.html(is_returns, output=is_report)

        if not combined_returns.empty:
            combined_report = os.path.join(
                market_output_directory,
                f"{market}_{lookback_period}_is_then_oos_report.html",
            )
            qs.reports.html(combined_returns, output=combined_report)


def generate_quantstats_reports_specific(is_df, oos_df):
    add_periods = config["modules"]["report"].get("add", {})
    remove_markets = config["modules"]["report"].get("remove", [])

    best_periods = {}
    all_returns_is = None
    all_returns_is_then_oos = None
    all_returns_oos = None

    cutoff_date = datetime.now() - timedelta(days=365 * 2)

    for market in is_df["Market"].unique():

        if market in remove_markets:
            continue

        best_lookback_period = None
        best_combined_sharpe = float("-inf")

        if market in add_periods:
            best_periods[market] = int(add_periods[market])
            continue

        for lookback_period in is_df["IS_QuarterCount"].unique():

            is_market_data = is_df[
                (is_df["Market"] == market)
                & (is_df["IS_QuarterCount"] == lookback_period)
            ]
            oos_market_data = oos_df[
                (oos_df["Market"] == market)
                & (oos_df["IS_QuarterCount"] == lookback_period)
            ]

            if is_market_data.empty:
                continue

            is_returns = prepare_market_data(is_market_data).loc[
                ~prepare_market_data(is_market_data).index.duplicated(keep="first")
            ]
            oos_returns = prepare_market_data(oos_market_data)

            if not oos_returns.empty:
                if oos_returns.index[-1] < cutoff_date:
                    continue

                switch_date = oos_returns.index[0]
                is_then_oos_returns = pd.concat(
                    [is_returns[is_returns.index < switch_date], oos_returns]
                )

                oos_sharpe = sharpe(oos_returns)
                is_then_oos_sharpe = sharpe(is_then_oos_returns)

                if oos_sharpe > 2 and is_then_oos_sharpe > 2:
                    combined_sharpe = 0.6 * oos_sharpe + 0.4 * is_then_oos_sharpe

                    if combined_sharpe > best_combined_sharpe:
                        best_combined_sharpe = combined_sharpe
                        best_lookback_period = lookback_period

        if best_lookback_period is not None:
            best_periods[market] = int(best_lookback_period)

    best_periods_file_path = os.path.join(specific_directory, "best_periods.json")
    with open(best_periods_file_path, "w") as json_file:
        json.dump(best_periods, json_file, indent=4)

    print("best_periods.json stored")

    for market, best_lookback_period in best_periods.items():
        is_market_data = is_df[
            (is_df["Market"] == market)
            & (is_df["IS_QuarterCount"] == best_lookback_period)
        ]
        oos_market_data = oos_df[
            (oos_df["Market"] == market)
            & (oos_df["IS_QuarterCount"] == best_lookback_period)
        ]

        is_returns = prepare_market_data(is_market_data).loc[
            ~prepare_market_data(is_market_data).index.duplicated(keep="first")
        ]
        oos_returns = prepare_market_data(oos_market_data)

        if not oos_returns.empty:
            switch_date = oos_returns.index[0]
            is_then_oos_returns = pd.concat(
                [is_returns[is_returns.index < switch_date], oos_returns]
            )

            if all_returns_oos is None:
                all_returns_oos = oos_returns
            else:
                all_returns_oos = all_returns_oos.add(oos_returns, fill_value=0)

            oos_report = os.path.join(
                output_directory_specific,
                f"{market}_{best_lookback_period}_best_oos_report.html",
            )
            qs.reports.html(oos_returns, output=oos_report)

        if not is_returns.empty:
            if all_returns_is is None:
                all_returns_is = is_returns
            else:
                all_returns_is = all_returns_is.add(is_returns, fill_value=0)

            is_report = os.path.join(
                output_directory_specific,
                f"{market}_{best_lookback_period}_best_is_report.html",
            )
            qs.reports.html(is_returns, output=is_report)

        if not is_then_oos_returns.empty:
            if all_returns_is_then_oos is None:
                all_returns_is_then_oos = is_then_oos_returns
            else:
                all_returns_is_then_oos = all_returns_is_then_oos.add(
                    is_then_oos_returns, fill_value=0
                )

            combined_report = os.path.join(
                output_directory_specific,
                f"{market}_{best_lookback_period}_best_is_then_oos_report.html",
            )
            qs.reports.html(is_then_oos_returns, output=combined_report)

    if all_returns_is is not None:
        all_returns_is = all_returns_is.fillna(0).sort_index()
        all_returns_is_path = os.path.join(
            output_directory_specific, "_all_returns_is.html"
        )
        qs.reports.html(
            all_returns_is,
            output=all_returns_is_path,
            title="All IS Returns (Best Lookback)",
        )

    if all_returns_is_then_oos is not None:
        all_returns_is_then_oos = all_returns_is_then_oos.fillna(0).sort_index()
        all_returns_is_then_oos_path = os.path.join(
            output_directory_specific, "_all_returns_is_then_oos.html"
        )
        qs.reports.html(
            all_returns_is_then_oos,
            output=all_returns_is_then_oos_path,
            title="All IS then OOS Returns (Best Lookback)",
        )

    if all_returns_oos is not None:
        all_returns_oos = all_returns_oos.fillna(0).sort_index()
        all_returns_oos_path = os.path.join(
            output_directory_specific, "_all_returns_oos.html"
        )
        qs.reports.html(
            all_returns_oos,
            output=all_returns_oos_path,
            title="All OOS Returns (Best Lookback)",
        )


generate_quantstats_reports_specific(is_df, oos_df)
generate_quantstats_reports(is_df, oos_df)
