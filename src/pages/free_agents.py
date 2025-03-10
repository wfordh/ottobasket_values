# add this https://ottoneu.fangraphs.com/basketball/average_values

import datetime
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st

from leagues import get_league_rosters  # type: ignore
from leagues import get_average_values, get_league_scoring
from pipeline import ottobasket_values_pipeline  # type: ignore
from transform import get_scoring_minutes_combo, prep_stats_df  # type: ignore


def ottoneu_streamlit_footer():
    # get a CachedStFunctionWarning when using this in a utils.py file and
    # with every page
    now = datetime.datetime.now(tz=ZoneInfo("US/Pacific"))
    st.markdown(
        "About page / README can be found [here](https://github.com/wfordh/ottobasket_values/blob/main/README.md)"
    )
    st.text("ros = rest of season. ytd = year to date.")
    st.text(f"Last updated: {now.strftime('%Y-%m-%d %I:%M %p (Pacific)')}")
    values_csv = convert_df(display_df)
    st.download_button(
        "Press to download",
        values_csv,
        "league_free_agents.csv",
        "text/csv",
        key="download-csv",
    )


def convert_df(df: pd.DataFrame) -> bytes:
    # Index is set to either player or team at all times
    return df.to_csv(index=True).encode("utf-8")


def select_format(x):
    if "sgp" in x:
        return "{:.1f}"
    elif x == "categories_value":
        return "${:.0f}"
    elif x not in ["player", "ottoneu_position"]:
        return "{:.0f}"
    else:
        return "{}"


stats_df = prep_stats_df()

league_input = st.sidebar.number_input("League ID", placeholder="1", min_value=1)
if league_input:
    try:
        league_salaries = get_league_rosters(league_input)
        # get league info
        league_scoring = get_league_scoring(league_input)
    except pd.errors.ParserError:
        st.error("Invalid league ID. Try again!")

    ros_df = get_scoring_minutes_combo("rest_of_season", stats_df, is_rollup=False)
    format_cols = {col: select_format(col) for col in ros_df.columns}

    league_values_df = ros_df.merge(league_salaries, on="ottoneu_player_id", how="left")
    league_values_df = league_values_df.loc[league_values_df.salary.isna()].copy()
    league_values_df.player.fillna(league_values_df.player_name, inplace=True)
    league_values_df.ottoneu_position.fillna(league_values_df.position, inplace=True)
    # fill the rest of columns NA's with 0
    league_values_df.fillna(0, inplace=True)
    if league_scoring == "categories":
        scoring_col = f"{league_scoring}_value"
    elif league_scoring == "simple_points":
        scoring_col = f"{league_scoring}_value"
    else:
        # Ottoneu has it as "traditional_points", need to shorten it to be consistent
        league_scoring = "trad_points"
        scoring_col = "trad_points_value"
    league_values_df[f"{league_scoring}_ppg"] = (
        league_values_df[f"{league_scoring}"] / league_values_df.games_forecast
    )
    average_values_df = get_average_values()
    league_values_df = league_values_df.merge(
        average_values_df, how="left", on="ottoneu_player_id"
    )
    display_cols = [
        "player",
        "ottoneu_position",
        "games_forecast",
        "total_ros_minutes",
        f"{league_scoring}",
        f"{league_scoring}_ppg",
        f"{league_scoring}_value",
        "avg_salary",
        "median_salary",
        "roster%",
    ]

    if league_scoring == "categories":
        display_cols.extend([col for col in league_values_df.columns if "sgp" in col])

    print(league_values_df.columns)
    display_df = league_values_df[display_cols].rename(
        columns={f"{league_scoring}": f"{league_scoring}_proj_production"}
    )

    display_df.sort_values(
        by=[f"{league_scoring}_value", f"{league_scoring}_proj_production"],
        ascending=False,
        inplace=True,
    )
    display_df.dropna(subset=f"{league_scoring}_ppg", inplace=True)
    display_df.set_index(
        "player", inplace=True
    )  # .reset_index(drop=True, inplace=True)
    # dropping the categories per game scoring until I come up with a better way
    # to display it...per 82 games?
    if league_scoring == "categories":
        display_df.drop(f"{league_scoring}_ppg", axis=1, inplace=True)
    format_cols.update(
        {
            f"{league_scoring}_proj_production": "{:.1f}",
            f"{league_scoring}_ppg": "{:.1f}",
        }
    )
    # this stuff not ready for prod...need to work on it more
    # display_df["is_drafted"] = False

    # st.data_editor(
    #     display_df.style.format(format_cols),
    #     column_config={
    #         "is_drafted": st.column_config.CheckboxColumn("Drafted?", default=False)
    #     },
    # )
    st.dataframe(display_df.style.format(format_cols))
    st.text("Free agents are sorted by projected rest of season value and production.")
else:
    st.markdown("Please input a league ID!")
    display_df = pd.DataFrame()


ottoneu_streamlit_footer()
