import logging
import os
import sys

import pandas as pd
import plottable as pt
from matplotlib import pyplot as plt

sys.path.append(os.path.abspath("src"))
logging.basicConfig(level=logging.INFO)


def main():
    pre_df = pd.read_csv("./data/pre_arb_values_2023.csv")
    post_df = pd.read_csv("./data/post_arb_values_2023.csv")

    all_values = pre_df.merge(
        post_df, how="left", on=["ID", "Name", "Position"], suffixes=("_pre", "_post")
    )
    new_cols = [col.lower().replace(" ", "_") for col in all_values.columns]
    all_values.columns = new_cols
    all_values = all_values[
        ["id", "name", "position", "ottoneu_av_pre", "ottoneu_av_post"]
    ]
    all_values["ottoneu_av_post"] = all_values.ottoneu_av_post.str.replace(
        "$", ""
    ).astype(float)
    all_values["ottoneu_av_pre"] = all_values.ottoneu_av_pre.str.replace(
        "$", ""
    ).astype(float)
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
    fig, ax = plt.subplots(figsize=(8, 5))
    raw_arb_table = pt.Table(
        all_values.drop(["id"], axis=1)
        .sort_values(by="arb_amount", ascending=False)
        .head(10)
        .set_index("name"),
        row_dividers=True,
        column_definitions=[
            pt.ColumnDefinition(
                name="name", title="Player\nName", textprops={"ha": "left"}
            ),
            pt.ColumnDefinition(name="position", title="Ottoneu\nPosition"),
            pt.ColumnDefinition(
                name="ottoneu_av_pre",
                title="Pre-Arb $",
                formatter="${:.2f}",
                border="left",
            ),
            pt.ColumnDefinition(
                name="ottoneu_av_post",
                title="Post-Arb $",
                formatter="${:.2f}",
                border="right",
            ),
            pt.ColumnDefinition(
                name="arb_amount", title="Arb $\nReceived", formatter="${:.2f}"
            ),
            pt.ColumnDefinition(
                name="arb_pct_prev_salary",
                title="% Salary\nIncrease",
                formatter=pt.formatters.decimal_to_percent,
            ),
        ],
        row_divider_kw={"linewidth": 1, "linestyle": (0, (1, 5))},
        ax=ax,
        even_row_color="#a9d8f5",
        odd_row_color="#f5c6a9",
    )
    fig.savefig("raw_arb_increasers.png")

    fig, ax = plt.subplots(figsize=(8, 5))
    pct_arb_table = pt.Table(
        all_values.drop(["id"], axis=1)
        .sort_values(by="arb_pct_prev_salary", ascending=False)
        .head(10)
        .set_index("name"),
        row_dividers=True,
        column_definitions=[
            pt.ColumnDefinition(
                name="name", title="Player\nName", textprops={"ha": "left"}
            ),
            pt.ColumnDefinition(name="position", title="Ottoneu\nPosition"),
            pt.ColumnDefinition(
                name="ottoneu_av_pre",
                title="Pre-Arb $",
                formatter="${:.2f}",
                border="left",
            ),
            pt.ColumnDefinition(
                name="ottoneu_av_post",
                title="Post-Arb $",
                formatter="${:.2f}",
                border="right",
            ),
            pt.ColumnDefinition(
                name="arb_amount", title="Arb $\nReceived", formatter="${:.2f}"
            ),
            pt.ColumnDefinition(
                name="arb_pct_prev_salary",
                title="% Salary\nIncrease",
                formatter=pt.formatters.decimal_to_percent,
            ),
        ],
        row_divider_kw={"linewidth": 1, "linestyle": (0, (1, 5))},
        ax=ax,
        even_row_color="#a9d8f5",
        odd_row_color="#f5c6a9",
    )

    fig.savefig("pct_arb_increasers.png")


if __name__ == "__main__":
    main()
