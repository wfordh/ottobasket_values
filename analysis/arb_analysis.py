# mypy: ignore-errors
import argparse
import logging
import os
import sys

import pandas as pd
from great_tables import GT, html, loc, md, style
from lets_plot import *  # type: ignore

sys.path.append(os.path.abspath("src"))
logging.basicConfig(level=logging.INFO)

parser = argparse.ArgumentParser()

parser.add_argument(
    "-s",
    "--season",
    help="The season to use for analysis. Must be a single year, eg 2023.",
    required=True,
    type=int,
)

# https://cdn.nba.com/headshots/nba/latest/1040x760/[PLAYER_ID].png


def main():
    args = parser.parse_args()
    command_args = dict(vars(args))
    season = command_args.pop("season", None)
    pre_df = pd.read_csv(f"./data/pre_arb_values_{season}.csv").rename(
        columns={"Avg Salary": "ottoneu_av"}
    )
    post_df = pd.read_csv(f"./data/post_arb_values_{season}.csv").rename(
        columns={"Avg Salary": "ottoneu_av"}
    )
    mappings = pd.read_csv("data/mappings_update_2023-09-14.csv")
    year_end_values = pd.read_csv(f"data/final_{season}_values.csv")
    leagues_info = pd.read_csv("data/league_settings.csv")

    all_values = pre_df.merge(
        post_df, how="left", on=["ID", "Name", "Position"], suffixes=("_pre", "_post")
    )
    new_cols = [col.lower().replace(" ", "_") for col in all_values.columns]
    all_values.columns = new_cols
    logging.info(all_values.columns)
    all_values = all_values[
        ["id", "name", "position", "ottoneu_av_pre", "ottoneu_av_post"]
    ].merge(
        mappings[["ottoneu_player_id", "nba_player_id"]],
        how="left",
        left_on="id",
        right_on="ottoneu_player_id",
    )
    all_values["nba_player_id"] = all_values.nba_player_id.fillna(0).astype(int)
    all_values["ottoneu_av_post"] = all_values.ottoneu_av_post.str.replace(
        "$", ""
    ).astype(float)
    all_values["ottoneu_av_pre"] = (
        all_values.ottoneu_av_pre.str.replace("$", "")
        .astype(float)
        .apply(lambda row: row + 3 if row.nba_player_id != 0 else row + 1)
    )
    all_values.dropna(inplace=True)
    all_values["arb_amount"] = (
        all_values.ottoneu_av_post - all_values.ottoneu_av_pre
    ).round(2)
    all_values["arb_pct_prev_salary"] = (
        all_values.arb_amount / all_values.ottoneu_av_pre
    )

    # some straightforward analysis
    logging.info(
        f"Top arb receivers: \n {all_values.sort_values(by='arb_amount', ascending=False).head(10)}"
    )
    logging.info(
        f"Top arb receivers as pctg of previous salary: \n {all_values.sort_values(by='arb_pct_prev_salary', ascending=False).head(10)}"
    )
    # table versions
    raw_arb_gt = (
        GT(
            all_values.sort_values(by="arb_amount", ascending=False)
            .head(10)
            .reset_index(drop=True)
        )
        .cols_hide(columns=["id", "ottoneu_player_id", "nba_player_id"])
        .cols_move_to_start("nba_player_id")
        # .fmt_image(columns="nba_player_id", file_pattern="https://cdn.nba.com/headshots/nba/latest/1040x760/{}.png")
        .tab_header(title="Top Arbitrated Players", subtitle="Raw Arb Dollars Received")
        .tab_spanner(
            label="Avg Ottoneu Salary", columns=["ottoneu_av_pre", "ottoneu_av_post"]
        )
        .tab_spanner(
            label="Arb Increases", columns=["arb_amount", "arb_pct_prev_salary"]
        )
        .cols_label(
            name="Name",
            position=html("Ottoneu<br>Position"),
            ottoneu_av_pre="Pre-Arb $",
            ottoneu_av_post="Post-Arb $",
            arb_amount="$ Received",
            arb_pct_prev_salary="% Increase",
            nba_player_id="",
        )
        .fmt_currency(
            columns=["ottoneu_av_pre", "ottoneu_av_post", "arb_amount"],
            currency="USD",
            decimals=2,
        )
        .fmt_percent(columns="arb_pct_prev_salary")
        .tab_style(
            style=style.fill("#a9d8f5"), locations=loc.body(rows=[0, 2, 4, 6, 8])
        )
        .tab_style(
            style=style.fill("#f5c6a9"), locations=loc.body(rows=[1, 3, 5, 7, 9])
        )
        .tab_style(
            style=style.borders(sides="left", style="solid", color="white"),
            locations=loc.body(columns=["ottoneu_av_pre", "arb_amount"]),
        )
        .tab_source_note(source_note=md("@wfordh | Data: Ottoneu Basketball"))
    )

    # raw_arb_gt.save(f"analysis/images/raw_arb_increasers_{season}_gt.png")

    pct_arb_gt = (
        GT(
            all_values.sort_values(by="arb_pct_prev_salary", ascending=False)
            .head(10)
            .reset_index(drop=True)
        )
        .cols_hide(columns=["id", "ottoneu_player_id", "nba_player_id"])
        .cols_move_to_start("nba_player_id")
        # .fmt_image(columns="nba_player_id", file_pattern="https://cdn.nba.com/headshots/nba/latest/1040x760/{}.png")
        .tab_header(
            title="Top Arbitrated Players", subtitle="Percentage Salary Increased"
        )
        .tab_spanner(
            label="Avg Ottoneu Salary", columns=["ottoneu_av_pre", "ottoneu_av_post"]
        )
        .tab_spanner(
            label="Arb Increases", columns=["arb_amount", "arb_pct_prev_salary"]
        )
        .cols_label(
            name="Name",
            position=html("Ottoneu<br>Position"),
            ottoneu_av_pre="Pre-Arb $",
            ottoneu_av_post="Post-Arb $",
            arb_amount="$ Received",
            arb_pct_prev_salary="% Increase",
            nba_player_id="",
        )
        .fmt_currency(
            columns=["ottoneu_av_pre", "ottoneu_av_post", "arb_amount"],
            currency="USD",
            decimals=2,
        )
        .fmt_percent(columns="arb_pct_prev_salary")
        .tab_style(
            style=style.fill("#a9d8f5"), locations=loc.body(rows=[0, 2, 4, 6, 8])
        )
        .tab_style(
            style=style.fill("#f5c6a9"), locations=loc.body(rows=[1, 3, 5, 7, 9])
        )
        .tab_style(
            style=style.borders(sides="left", style="solid", color="white"),
            locations=loc.body(columns=["ottoneu_av_pre", "arb_amount"]),
        )
        .tab_source_note(source_note=md("@wfordh | Data: Ottoneu Basketball"))
    )

    # pct_arb_gt.save(f"analysis/images/pct_arb_increasers_{season}_gt.png")

    all_values = all_values.merge(
        year_end_values, how="left", on=["ottoneu_player_id", "nba_player_id"]
    )

    all_values["nba_player_id"] = all_values.nba_player_id.astype(str)

    # how to define? arb > 0? arb < half of median arb?
    arb_median = all_values.loc[all_values.arb_amount > 0].arb_amount.median()
    arb_mean = all_values.loc[all_values.arb_amount > 0].arb_amount.mean()
    # wish I could weight by number of leagues...
    # 8 cats, 2 simple, 10 trad
    points_system_dist = (
        leagues_info.groupby("points_system").league_id.count().to_dict()
    )
    total_leagues = sum(points_system_dist.values())
    all_values["avg_value_ytd"] = (
        points_system_dist["Categories"] * all_values.categories_value_ytd
        + points_system_dist["Simple Points"] * all_values.simple_points_value_ytd
        + points_system_dist["Traditional Points"] * all_values.trad_points_value_ytd
    ) / total_leagues

    all_values["post_arb_surplus"] = (
        all_values.avg_value_ytd - all_values.ottoneu_av_post
    )
    all_values.drop(
        [
            "categories_value_ytd",
            "trad_points_value_ytd",
            "simple_points_value_ytd",
            "player",
            "ottoneu_position",
        ],
        axis=1,
        inplace=True,
    )
    logging.info(
        f"""Most remaining post-arb surplus (rec'd arb & less than 1.5*mean):\n
        {all_values.loc[
                    (all_values.arb_amount < 1.5*arb_mean) & (all_values.arb_amount > 0)
                ]
                .sort_values(by="post_arb_surplus", ascending=False)
                .head(10)}
        """
    )
    most_post_arb_surplus_gt = (
        GT(
            all_values.loc[
                (all_values.arb_amount < 1.5 * arb_mean) & (all_values.arb_amount > 0)
            ]
            .sort_values(by="post_arb_surplus", ascending=False)
            .head(10)
            .reset_index(drop=True)
        )
        .tab_header(
            title="Top Post-Arb Surplus Players", subtitle="Excluding top arb receivers"
        )
        .tab_spanner(
            columns=["ottoneu_av_post", "arb_amount"], label="Ottoneu Measures"
        )
        .tab_spanner(
            columns=["avg_value_ytd", "post_arb_surplus"],
            label="Value Derived Measures",
        )
        .cols_hide(
            columns=[
                "id",
                "ottoneu_player_id",
                "nba_player_id",
                "minutes_ytd",
                "ottoneu_av_pre",
                "arb_pct_prev_salary",
            ]
        )
        .cols_label(
            name="Name",
            position="Ottoneu Position",
            ottoneu_av_post="Post-Arb $",
            arb_amount="$ Received",
            avg_value_ytd="Weighted Avg $ Value",
            post_arb_surplus="Post-Arb $ Surplus",
        )
        .fmt_currency(
            columns=[
                "ottoneu_av_post",
                "arb_amount",
                "avg_value_ytd",
                "post_arb_surplus",
            ],
            currency="USD",
            decimals=2,
        )
        .tab_style(
            style=style.fill("#a9d8f5"), locations=loc.body(rows=[0, 2, 4, 6, 8])
        )
        .tab_style(
            style=style.fill("#f5c6a9"), locations=loc.body(rows=[1, 3, 5, 7, 9])
        )
        .tab_style(
            style=style.borders(sides="left", style="solid", color="white"),
            locations=loc.body(columns=["ottoneu_av_post", "avg_value_ytd"]),
        )
        .tab_source_note(source_note=md("@wfordh | Data: Ottoneu Basketball"))
    )
    most_post_arb_surplus_gt.save(
        f"analysis/images/post_arb_surplus_{season}_limited.png"
    )

    logging.info(
        f"Most remaining post-arb surplus (all):\n {all_values.sort_values(by='post_arb_surplus', ascending=False).head(10)}"
    )
    most_post_arb_surplus_all_gt = (
        GT(
            all_values.sort_values(by="post_arb_surplus", ascending=False)
            .head(10)
            .reset_index(drop=True)
        )
        .tab_header(title="Top Post-Arb Surplus Players", subtitle="All Players")
        .tab_spanner(
            columns=["ottoneu_av_post", "arb_amount"], label="Ottoneu Measures"
        )
        .tab_spanner(
            columns=["avg_value_ytd", "post_arb_surplus"],
            label="Value Derived Measures",
        )
        .cols_hide(
            columns=[
                "id",
                "ottoneu_player_id",
                "nba_player_id",
                "minutes_ytd",
                "ottoneu_av_pre",
                "arb_pct_prev_salary",
            ]
        )
        .cols_label(
            name="Name",
            position="Ottoneu Position",
            ottoneu_av_post="Post-Arb $",
            arb_amount="$ Received",
            avg_value_ytd="Weighted Avg $ Value",
            post_arb_surplus="Post-Arb $ Surplus",
        )
        .fmt_currency(
            columns=[
                "ottoneu_av_post",
                "arb_amount",
                "avg_value_ytd",
                "post_arb_surplus",
            ],
            currency="USD",
            decimals=2,
        )
        .tab_style(
            style=style.fill("#a9d8f5"), locations=loc.body(rows=[0, 2, 4, 6, 8])
        )
        .tab_style(
            style=style.fill("#f5c6a9"), locations=loc.body(rows=[1, 3, 5, 7, 9])
        )
        .tab_style(
            style=style.borders(sides="left", style="solid", color="white"),
            locations=loc.body(columns=["ottoneu_av_post", "avg_value_ytd"]),
        )
        .tab_source_note(source_note=md("@wfordh | Data: Ottoneu Basketball"))
    )

    most_post_arb_surplus_all_gt.save(
        f"analysis/images/post_arb_surplus_{season}_all.png"
    )

    logging.info(
        f"biggest arb receivers for neg surplus:\n {all_values.loc[all_values.post_arb_surplus < 0].sort_values(by='arb_amount', ascending=False).head(10)}"
    )
    neg_surplus_arb_receivers_gt = (
        GT(
            all_values.loc[all_values.post_arb_surplus < 0]
            .sort_values(by="arb_amount", ascending=False)
            .head(10)
            .reset_index(drop=True)
        )
        .tab_header(
            title="Most Arb Dollars Received by Negative Surplus Players",
            subtitle="Using Post-Arb Salaries and Season Values",
        )
        .tab_spanner(
            columns=["ottoneu_av_post", "arb_amount"], label="Ottoneu Measures"
        )
        .tab_spanner(
            columns=["avg_value_ytd", "post_arb_surplus"],
            label="Value Derived Measures",
        )
        .cols_hide(
            columns=[
                "id",
                "ottoneu_player_id",
                "nba_player_id",
                "minutes_ytd",
                "ottoneu_av_pre",
                "arb_pct_prev_salary",
            ]
        )
        .cols_label(
            name="Name",
            position="Ottoneu Position",
            ottoneu_av_post="Post-Arb $",
            arb_amount="$ Received",
            avg_value_ytd="Weighted Avg $ Value",
            post_arb_surplus="Post-Arb $ Surplus",
        )
        .fmt_currency(
            columns=[
                "ottoneu_av_post",
                "arb_amount",
                "avg_value_ytd",
                "post_arb_surplus",
            ],
            currency="USD",
            decimals=2,
        )
        .tab_style(
            style=style.fill("#a9d8f5"), locations=loc.body(rows=[0, 2, 4, 6, 8])
        )
        .tab_style(
            style=style.fill("#f5c6a9"), locations=loc.body(rows=[1, 3, 5, 7, 9])
        )
        .tab_style(
            style=style.borders(sides="left", style="solid", color="white"),
            locations=loc.body(columns=["ottoneu_av_post", "avg_value_ytd"]),
        )
        .tab_source_note(source_note=md("@wfordh | Data: Ottoneu Basketball"))
    )

    neg_surplus_arb_receivers_gt.save(
        f"analysis/images/neg_surplus_arb_receivers_{season}.png"
    )

    arb_receivers_most_negative_gt = (
        GT(
            all_values.loc[all_values.arb_amount > 0]
            .sort_values(by="post_arb_surplus", ascending=True)
            .head(10)
            .reset_index(drop=True)
        )
        .tab_header(
            title="Most Negative Surplus Players who Received Arb $",
            subtitle="Using Post-Arb Salaries and Season Values",
        )
        .tab_spanner(
            columns=["ottoneu_av_post", "arb_amount"], label="Ottoneu Measures"
        )
        .tab_spanner(
            columns=["avg_value_ytd", "post_arb_surplus"],
            label="Value Derived Measures",
        )
        .cols_hide(
            columns=[
                "id",
                "ottoneu_player_id",
                "nba_player_id",
                "minutes_ytd",
                "ottoneu_av_pre",
                "arb_pct_prev_salary",
            ]
        )
        .cols_label(
            name="Name",
            position="Ottoneu Position",
            ottoneu_av_post="Post-Arb $",
            arb_amount="$ Received",
            avg_value_ytd="Weighted Avg $ Value",
            post_arb_surplus="Post-Arb $ Surplus",
        )
        .fmt_currency(
            columns=[
                "ottoneu_av_post",
                "arb_amount",
                "avg_value_ytd",
                "post_arb_surplus",
            ],
            currency="USD",
            decimals=2,
        )
        .tab_style(
            style=style.fill("#a9d8f5"), locations=loc.body(rows=[0, 2, 4, 6, 8])
        )
        .tab_style(
            style=style.fill("#f5c6a9"), locations=loc.body(rows=[1, 3, 5, 7, 9])
        )
        .tab_style(
            style=style.borders(sides="left", style="solid", color="white"),
            locations=loc.body(columns=["ottoneu_av_post", "avg_value_ytd"]),
        )
        .tab_source_note(source_note=md("@wfordh | Data: Ottoneu Basketball"))
    )

    arb_receivers_most_negative_gt.save(
        f"analysis/images/arb_receivers_most_negative_{season}.png"
    )

    all_values["salary_pct_surplus"] = (
        all_values.ottoneu_av_post / all_values.avg_value_ytd
    )
    # all_values["player_img"] = all_values.nba_player_id.apply(lambda x: f"<img src='https://cdn.nba.com/headshots/nba/latest/1040x760/{x}.png' style = 'height:25px;'>")
    # print(all_values[["nba_player_id", "name"]].head())

    salary_pct_surplus_gt = (
        GT(
            all_values.loc[all_values.arb_amount > 0]
            .sort_values(by="salary_pct_surplus", ascending=True)
            .head(10)
            .reset_index(drop=True)
        )
        .tab_header(
            title="Players with Lowest Salary Relative to Surplus",
            subtitle="Among Players Receiving Arb",
        )
        .tab_spanner(
            columns=["ottoneu_av_post", "arb_amount"], label="Ottoneu Measures"
        )
        .tab_spanner(
            columns=["avg_value_ytd", "post_arb_surplus", "salary_pct_surplus"],
            label="Value Derived Measures",
        )
        .cols_hide(
            columns=[
                "id",
                "ottoneu_player_id",
                "nba_player_id",
                "minutes_ytd",
                "ottoneu_av_pre",
                "arb_pct_prev_salary",
            ]
        )
        .cols_label(
            name="Name",
            position="Ottoneu Position",
            ottoneu_av_post="Post-Arb $",
            arb_amount="$ Received",
            avg_value_ytd="Weighted Avg $ Value",
            post_arb_surplus="Post-Arb $ Surplus",
            salary_pct_surplus="Salary Share of Value",
        )
        .fmt_currency(
            columns=[
                "ottoneu_av_post",
                "arb_amount",
                "avg_value_ytd",
                "post_arb_surplus",
            ],
            currency="USD",
            decimals=2,
        )
        .fmt_percent(columns=["salary_pct_surplus"])
        # .fmt_image(columns="player_img")
        .tab_style(
            style=style.fill("#a9d8f5"), locations=loc.body(rows=[0, 2, 4, 6, 8])
        )
        .tab_style(
            style=style.fill("#f5c6a9"), locations=loc.body(rows=[1, 3, 5, 7, 9])
        )
        .tab_style(
            style=style.borders(sides="left", style="solid", color="white"),
            locations=loc.body(columns=["ottoneu_av_post", "avg_value_ytd"]),
        )
        .tab_source_note(source_note=md("@wfordh | Data: Ottoneu Basketball"))
    )

    salary_pct_surplus_gt.save(
        f"analysis/images/lowest_salary_pct_surplus_{season}.png"
    )

    surplus_vs_arb = (
        ggplot(
            all_values.loc[all_values.arb_amount > 0],
            aes(x="post_arb_surplus", y="arb_amount"),
        )
        + geom_point()
        + labs(
            x="Post-Arb Surplus ($)",
            y="Arb Amount ($)",
            title="Arbitration Dollars vs Post-Arb Surplus",
            subtitle="Among Players Receiving Arb",
            color="Ottoneu Position",
        )
        + coord_cartesian(xlim=(-75, 75))
    )

    ggsave(
        surplus_vs_arb, f"surplus_vs_arb_{season}.png", path="analysis/images/", scale=2
    )

    logging.info(
        f"The total post-arb surplus for players who received arb is {all_values.loc[all_values.arb_amount > 0].post_arb_surplus.sum()}"
    )
    logging.info(
        f"{all_values.loc[all_values.post_arb_surplus > 0].arb_amount.value_counts(normalize=True, ascending=True)}"
    )
    logging.info(
        f"{all_values.loc[(all_values.post_arb_surplus > 0) & (all_values.arb_amount == 0)][['name', 'post_arb_surplus', 'ottoneu_av_post']]}"
    )


if __name__ == "__main__":
    main()
