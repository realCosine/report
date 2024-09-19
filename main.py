import os
import json
import quantstats as qs
import pandas as pd
from datetime import datetime, timedelta
from itertools import product
from pathlib import Path

from src.report import *

qs.extend_pandas()


def generate_quantstats_reports(cfg: Config, is_df, oos_df):
    if cfg.report.generate_general is False:
        return

    combined_returns = None
    markets = is_df["Market"].unique()

    output_directory = cfg.report.output_dir_general
    for market, lookback_period in product(markets, is_df["IS_QuarterCount"].unique()):
        market_output_directory = output_directory / market
        os.makedirs(market_output_directory, exist_ok=True)

        is_market_data = is_df[
            (is_df["Market"] == market) & (is_df["IS_QuarterCount"] == lookback_period)
        ]
        oos_market_data = oos_df[
            (oos_df["Market"] == market)
            & (oos_df["IS_QuarterCount"] == lookback_period)
        ]

        is_returns = prepare_df_for_sharpe(is_market_data).loc[
            ~prepare_df_for_sharpe(is_market_data).index.duplicated(keep="first")
        ]
        oos_returns = prepare_df_for_sharpe(oos_market_data)

        if not oos_returns.empty:
            switch_date = oos_returns.index[0]
            combined_returns = pd.concat(
                [is_returns[is_returns.index < switch_date], oos_returns]
            )

            oos_report = (
                market_output_directory / f"{market}_{lookback_period}_oos_report.html"
            )
            qs.reports.html(oos_returns, output=oos_report)
        else:
            combined_returns = is_returns

        if not is_returns.empty:
            is_report = (
                market_output_directory / f"{market}_{lookback_period}_is_report.html"
            )

            qs.reports.html(is_returns, output=is_report)

            is_until_oos_returns = is_returns[
                is_returns.index <= oos_returns.index.min()
            ]

            if not is_until_oos_returns.empty:
                is_until_oos_report = (
                    market_output_directory
                    / f"{market}_{lookback_period}_is_until_oos_report.html"
                )
                qs.reports.html(is_until_oos_returns, output=is_until_oos_report)

        if not combined_returns.empty:
            combined_report = (
                market_output_directory
                / f"{market}_{lookback_period}_is_then_oos_report.html"
            )
            qs.reports.html(combined_returns, output=combined_report)


def generate_quantstats_reports_specific(cfg: Config, is_df, oos_df):
    if cfg.report.generate_specific is False:
        return

    specific_dir = cfg.report.output_dir_specific
    add_periods = cfg.report.specific.add
    remove_markets = cfg.report.specific.remove

    best_periods = {}
    all_returns_is = None
    all_returns_oos = None
    all_returns_is_then_oos = None
    all_returns_is_until_oos = None

    for market in is_df["Market"].unique():

        if market in remove_markets:
            continue

        best_lookback_period = None
        best_combined_sharpe = float("-inf")

        if market in add_periods and add_periods[market] != "?":
            best_periods[market] = {
                "lookback_period": int(add_periods[market]),
                "sharpe": None,
            }
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

            is_returns = prepare_df_for_sharpe(is_market_data).loc[
                ~prepare_df_for_sharpe(is_market_data).index.duplicated(keep="first")
            ]
            oos_returns = prepare_df_for_sharpe(oos_market_data)

            if not oos_returns.empty:
                switch_date = oos_returns.index[0]
                is_then_oos_returns = pd.concat(
                    [is_returns[is_returns.index < switch_date], oos_returns]
                )

                oos_sharpe = sharpe(oos_returns)
                is_then_oos_sharpe = sharpe(is_then_oos_returns)

                if oos_sharpe > 2.5 and is_then_oos_sharpe > 2:
                    combined_sharpe = 0.6 * oos_sharpe + 0.4 * is_then_oos_sharpe

                    if combined_sharpe > best_combined_sharpe:
                        best_combined_sharpe = combined_sharpe
                        best_lookback_period = lookback_period

        if best_lookback_period is not None:
            best_periods[market] = {
                "lookback_period": int(best_lookback_period),
                "sharpe": round(best_combined_sharpe, 3),
            }
    best_periods_file_path = cfg.core.output_dir / "best_periods.json"
    with open(best_periods_file_path, "w") as json_file:
        json.dump(best_periods, json_file, indent=4)

    print("best_periods.json stored")

    for market, data in best_periods.items():
        best_lookback_period = data["lookback_period"]

        is_market_data = is_df[
            (is_df["Market"] == market)
            & (is_df["IS_QuarterCount"] == best_lookback_period)
        ]
        oos_market_data = oos_df[
            (oos_df["Market"] == market)
            & (oos_df["IS_QuarterCount"] == best_lookback_period)
        ]

        is_returns = prepare_df_for_sharpe(is_market_data).loc[
            ~prepare_df_for_sharpe(is_market_data).index.duplicated(keep="first")
        ]
        oos_returns = prepare_df_for_sharpe(oos_market_data)

        if not oos_returns.empty:
            switch_date = oos_returns.index[0]
            is_then_oos_returns = pd.concat(
                [is_returns[is_returns.index < switch_date], oos_returns]
            )

            if all_returns_oos is None:
                all_returns_oos = oos_returns
            else:
                all_returns_oos = all_returns_oos.add(oos_returns, fill_value=0)

            oos_report = (
                specific_dir / f"{market}_{best_lookback_period}_best_oos_report.html"
            )
            qs.reports.html(oos_returns, output=oos_report)

        if not is_returns.empty:
            if all_returns_is is None:
                all_returns_is = is_returns
            else:
                all_returns_is = all_returns_is.add(is_returns, fill_value=0)

            is_report = (
                specific_dir / f"{market}_{best_lookback_period}_best_is_report.html"
            )
            qs.reports.html(is_returns, output=is_report)

            is_until_oos_returns = is_returns[
                is_returns.index <= oos_returns.index.min()
            ]

            if not is_until_oos_returns.empty:
                if all_returns_is_until_oos is None:
                    all_returns_is_until_oos = is_until_oos_returns
                else:
                    all_returns_is_until_oos = all_returns_is_until_oos.add(
                        is_until_oos_returns, fill_value=0
                    )

                is_until_oos_report = (
                    specific_dir
                    / f"{market}_{best_lookback_period}_best_is_until_oos_report.html"
                )
                qs.reports.html(is_until_oos_returns, output=is_until_oos_report)

        if not is_then_oos_returns.empty:
            if all_returns_is_then_oos is None:
                all_returns_is_then_oos = is_then_oos_returns
            else:
                all_returns_is_then_oos = all_returns_is_then_oos.add(
                    is_then_oos_returns, fill_value=0
                )

            combined_report = (
                specific_dir
                / f"{market}_{best_lookback_period}_best_is_then_oos_report.html"
            )
            qs.reports.html(is_then_oos_returns, output=combined_report)

    if all_returns_is is not None:
        all_returns_is = all_returns_is.fillna(0).sort_index()
        all_returns_is_path = specific_dir / "_all_returns_is.html"

        qs.reports.html(
            all_returns_is,
            output=all_returns_is_path,
            title="All IS Returns (Best Lookback)",
        )

        if all_returns_is_until_oos is not None:

            all_returns_is_until_oos_path = (
                specific_dir / "_all_returns_is_until_oos.html"
            )
            qs.reports.html(
                all_returns_is_until_oos,
                output=all_returns_is_until_oos_path,
                title="All IS Returns until OOS begins (Best Lookback)",
            )

    if all_returns_is_then_oos is not None:
        all_returns_is_then_oos = all_returns_is_then_oos.fillna(0).sort_index()
        all_returns_is_then_oos_path = specific_dir / "_all_returns_is_then_oos.html"

        qs.reports.html(
            all_returns_is_then_oos,
            output=all_returns_is_then_oos_path,
            title="All IS then OOS Returns (Best Lookback)",
        )

    if all_returns_oos is not None:
        all_returns_oos = all_returns_oos.fillna(0).sort_index()
        all_returns_oos_path = specific_dir / "_all_returns_oos.html"

        qs.reports.html(
            all_returns_oos,
            output=all_returns_oos_path,
            title="All OOS Returns (Best Lookback)",
        )


def combine_systems(cfg: Config):
    """
    Combines multiple systems' in-sample and out-of-sample DataFrames to generate
    aggregated QuantStats reports per market.

    Args:
        cfg (Config): Configuration object containing report settings.
    """
    if not cfg.report.combine_systems.enable:
        return

    systems_cfg = cfg.report.combine_systems.systems_config
    output_dir = cfg.report.output_dir_combined

    systems = []

    for system_dir, system_config in systems_cfg.items():
        risk = float(system_config.risk)
        add_periods = system_config.add
        remove_markets = system_config.remove

        is_path = system_dir / cfg.core.is_file_name
        oos_path = system_dir / cfg.core.oos_file_name

        if not is_path.exists() or not oos_path.exists():
            print(
                f"Missing is_data.csv or oos_data.csv in {system_dir}. Skipping this system."
            )
            continue

        system_is_df = pd.read_csv(is_path, parse_dates=True, index_col=0)
        system_oos_df = pd.read_csv(oos_path, parse_dates=True, index_col=0)

        system_is_df["ProfitPercent"] *= risk
        system_oos_df["ProfitPercent"] *= risk

        systems.append(
            {
                "path": system_dir,
                "is_df": system_is_df,
                "oos_df": system_oos_df,
                "add_periods": add_periods,
                "remove_markets": remove_markets,
            }
        )

    best_periods = {}
    for system in systems:
        system_path = system["path"]
        is_df = system["is_df"]
        oos_df = system["oos_df"]
        add_periods = system["add_periods"]
        remove_markets = system["remove_markets"]

        for market in is_df["Market"].unique():
            if remove_markets is not None and market in remove_markets:
                continue

            if market in add_periods and add_periods[market] != "?":
                if market not in best_periods:
                    best_periods[market] = {}
                best_periods[market][system_path] = int(add_periods[market])
                continue

            best_lookback_period = None
            best_combined_sharpe = float("-inf")

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

                is_returns = prepare_df_for_sharpe(is_market_data).loc[
                    ~prepare_df_for_sharpe(is_market_data).index.duplicated(
                        keep="first"
                    )
                ]
                oos_returns = prepare_df_for_sharpe(oos_market_data)

                if not oos_returns.empty:
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
                best_periods.setdefault(market, {})[system_path] = int(best_lookback_period)

    best_periods_file_path = output_dir / "best_periods.json"
    with open(best_periods_file_path, "w") as json_file:
        json.dump(parse_posix_paths(best_periods), json_file, indent=4)

    total_combined_is_returns = None
    total_combined_oos_returns = None
    total_combined_is_then_oos_returns = None

    for market in best_periods:
        market_combined_is_returns = None
        market_combined_oos_returns = None
        market_combined_is_then_oos_returns = None

        for system_path_str in best_periods[market]:
            system_path = Path(system_path_str)
            best_lookback_period = best_periods[market][system_path_str]
            system = next((s for s in systems if s["path"] == system_path), None)
            if system is None:
                continue

            is_df = system["is_df"]
            oos_df = system["oos_df"]
            is_market_data = is_df[
                (is_df["Market"] == market)
                & (is_df["IS_QuarterCount"] == best_lookback_period)
            ]
            oos_market_data = oos_df[
                (oos_df["Market"] == market)
                & (oos_df["IS_QuarterCount"] == best_lookback_period)
            ]
            if is_market_data.empty:
                continue

            is_returns = prepare_df_for_sharpe(is_market_data).loc[
                ~prepare_df_for_sharpe(is_market_data).index.duplicated(keep="first")
            ]
            oos_returns = prepare_df_for_sharpe(oos_market_data)

            if market_combined_is_returns is None:
                market_combined_is_returns = is_returns
            else:
                market_combined_is_returns = market_combined_is_returns.add(
                    is_returns, fill_value=0
                )

            if not oos_returns.empty:
                if market_combined_oos_returns is None:
                    market_combined_oos_returns = oos_returns
                else:
                    market_combined_oos_returns = market_combined_oos_returns.add(
                        oos_returns, fill_value=0
                    )

            switch_date = oos_returns.index[0] if not oos_returns.empty else None
            if switch_date is not None:
                is_until_switch = is_returns[is_returns.index < switch_date]
                is_then_oos_returns = pd.concat([is_until_switch, oos_returns])
            else:
                is_then_oos_returns = is_returns
            if market_combined_is_then_oos_returns is None:
                market_combined_is_then_oos_returns = is_then_oos_returns
            else:
                market_combined_is_then_oos_returns = (
                    market_combined_is_then_oos_returns.add(
                        is_then_oos_returns, fill_value=0
                    )
                )

        if market_combined_is_returns is not None:
            market_combined_is_returns = market_combined_is_returns.fillna(
                0
            ).sort_index()
            is_report_path = output_dir / f"{market}_best_is_report.html"
            qs.reports.html(
                market_combined_is_returns,
                output=is_report_path,
                title=f"Combined IS Report for {market}",
            )

            if total_combined_is_returns is None:
                total_combined_is_returns = market_combined_is_returns
            else:
                total_combined_is_returns = total_combined_is_returns.add(
                    market_combined_is_returns, fill_value=0
                )

        if market_combined_oos_returns is not None:
            market_combined_oos_returns = market_combined_oos_returns.fillna(
                0
            ).sort_index()
            oos_report_path = output_dir / f"{market}_best_oos_report.html"
            qs.reports.html(
                market_combined_oos_returns,
                output=oos_report_path,
                title=f"Combined OOS Report for {market}",
            )

            if total_combined_oos_returns is None:
                total_combined_oos_returns = market_combined_oos_returns
            else:
                total_combined_oos_returns = total_combined_oos_returns.add(
                    market_combined_oos_returns, fill_value=0
                )

        if market_combined_is_then_oos_returns is not None:
            market_combined_is_then_oos_returns = (
                market_combined_is_then_oos_returns.fillna(0).sort_index()
            )
            is_then_oos_report_path = (
                output_dir / f"{market}_best_is_then_oos_report.html"
            )
            qs.reports.html(
                market_combined_is_then_oos_returns,
                output=is_then_oos_report_path,
                title=f"Combined IS then OOS Report for {market}",
            )

            if total_combined_is_then_oos_returns is None:
                total_combined_is_then_oos_returns = market_combined_is_then_oos_returns
            else:
                total_combined_is_then_oos_returns = (
                    total_combined_is_then_oos_returns.add(
                        market_combined_is_then_oos_returns, fill_value=0
                    )
                )

    if total_combined_is_returns is not None:
        total_combined_is_returns = total_combined_is_returns.fillna(0).sort_index()
        total_is_report_path = output_dir / f"all_returns_is.html"
        qs.reports.html(
            total_combined_is_returns,
            output=total_is_report_path,
            title=f"Total Combined IS Report",
        )

    if total_combined_oos_returns is not None:
        total_combined_oos_returns = total_combined_oos_returns.fillna(0).sort_index()
        total_oos_report_path = output_dir / f"all_returns_oos.html"
        qs.reports.html(
            total_combined_oos_returns,
            output=total_oos_report_path,
            title=f"Total Combined OOS Report",
        )

    if total_combined_is_then_oos_returns is not None:
        total_combined_is_then_oos_returns = total_combined_is_then_oos_returns.fillna(
            0
        ).sort_index()
        total_is_then_oos_report_path = output_dir / f"all_returns_is_then_oos.html"
        qs.reports.html(
            total_combined_is_then_oos_returns,
            output=total_is_then_oos_report_path,
            title=f"Total Combined IS then OOS Report",
        )


if __name__ == "__main__":
    cfg = load_config()

    is_df = pd.read_csv(cfg.core.is_dir)
    oos_df = pd.read_csv(cfg.core.oos_dir)

    generate_quantstats_reports_specific(cfg, is_df.copy(), oos_df.copy())
    generate_quantstats_reports(cfg, is_df.copy(), oos_df.copy())
    combine_systems(cfg)
