import json
from typing import Optional

import gspread  # type: ignore
import pandas as pd


def _setup_gdrive(client_key_string: Optional[str]) -> gspread.client.Client:
    credentials = json.loads(client_key_string)  # type: ignore
    return gspread.service_account_from_dict(credentials)


def _upload_data(
    gc: gspread.client.Client,
    data: pd.DataFrame,
    sheet_key: str,
    wks_num: int = 0,
    clear: bool = False,
) -> None:
    """Uploads data to the provided Google sheet."""
    sheet = gc.open_by_key(sheet_key)
    worksheet = sheet.get_worksheet(wks_num)
    if clear:
        worksheet.clear()
    worksheet.update([data.columns.values.tolist()] + data.values.tolist())


def get_existing_sgp_data() -> pd.DataFrame:
    sheet_key = "17NoW7CT-AvQ9-VtT22nzaXnVCYNgunGDlYeDeDEn_Mc"
    return pd.read_csv(
        f"https://docs.google.com/spreadsheets/d/{sheet_key}/gviz/tq?tqx=out:csv&gid=284274620"
    )


def get_sgp_rollup() -> pd.DataFrame:
    gid = "56814419"
    sheet_key = "17NoW7CT-AvQ9-VtT22nzaXnVCYNgunGDlYeDeDEn_Mc"
    return pd.read_csv(
        f"https://docs.google.com/spreadsheets/d/{sheet_key}/gviz/tq?tqx=out:csv&gid={gid}"
    )


def get_leagues_metadata() -> pd.DataFrame:
    sheet_key = "14TkjXjFSWDQsHZy6Qt77elLnVpi1HwrpbqzVC4JKDjc"
    return pd.read_csv(
        f"https://docs.google.com/spreadsheets/d/{sheet_key}/export?format=csv&gid=0"
    )


def get_name_map() -> pd.DataFrame:
    """Gets the mapping for names and IDs."""
    return pd.read_csv("./data/mappings_update_2023-09-14.csv")


def get_hashtag_ros_projections() -> pd.DataFrame:
    """Gets the hashtagbasketball projections from the Google sheet."""
    sheet_id = "1RiXnGk2OFnGRmW9QNQ_1CFde0xfSZpyC9Cn3OLLojsY"  # env variable?
    df = pd.read_csv(
        f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid=0"
    )
    return df[["name", "pid", "games_forecast", "minutes_forecast"]]


def get_hashtag_rookie_projections() -> pd.DataFrame:
    sheet_id = "1RiXnGk2OFnGRmW9QNQ_1CFde0xfSZpyC9Cn3OLLojsY"  # env variable?
    df = pd.read_csv(
        f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid=0"
    )
    rookies = pd.read_csv("data/rookies.csv")
    # print(rookies)
    hashtag_rookies = [int(pid) for pid in rookies.hashtag_id.dropna().tolist()]
    return df.loc[df.pid.isin(hashtag_rookies)]


def get_ottoneu_leaderboard() -> pd.DataFrame:
    """Gets the results from the Ottoneu leaderboard for the current season."""
    return pd.read_csv(
        "https://ottoneu.fangraphs.com/basketball/31/ajax/player_leaderboard?positions[]=G&positions[]=F&positions[]=C&minimum_minutes=0&sort_by=salary&sort_direction=DESC&free_agents_only=false&include_my_team=false&export=export"
    ).rename(columns={"id": "ottoneu_player_id"})
