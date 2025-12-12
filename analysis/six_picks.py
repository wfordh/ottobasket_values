# cribbed from here: https://medium.com/ml-everything/using-python-and-linear-programming-to-optimize-fantasy-football-picks-dc9d1229db81
# but this prob better: https://github.com/ashhhlynn/custom-fantasy-optimizer
# and this: https://github.com/galactusaurus/df_optimization/blob/main/optimize_roster.py

import os
import re
import sys
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup
from PIL import Image
from pulp import PULP_CBC_CMD, LpMaximize, LpProblem, LpVariable, lpSum

sys.path.append(os.path.abspath("src"))

from utils import get_name_map

SALARY_CAP = 180


def get_player_headshot(nba_id: int):
    url = f"https://cdn.nba.com/headshots/nba/latest/1040x760/{nba_id}.png"
    return requests.get(url, stream=True)


def cleanup_and_save_images(player_ids: list, mappings: pd.DataFrame):
    ids = mappings.loc[
        mappings.ottoneu_player_id.isin(player_ids),
        ["nba_player_id", "ottoneu_player_id"],
    ].values.tolist()
    img_dir = Path("./analysis/six_picks_images/")
    assert img_dir.exists()
    for file in img_dir.iterdir():
        if file.suffix == ".png":
            file.unlink()

    for nba_id, otto_id in ids:
        resp = get_player_headshot(int(nba_id))
        with open(img_dir / f"six_picks_{int(otto_id)}.png", "wb") as out_file:
            Image.open(resp.raw).save(out_file)
        del resp


def get_sixpicks_leaderboard(date: str) -> pd.DataFrame:
    url = f"https://ottoneu.fangraphs.com/sixpicks/basketball/board/{date}"
    resp = requests.get(url)
    soup = BeautifulSoup(resp.content, "html.parser")
    table = soup.find("div", {"class": "left"}).find("table")
    headers = [
        th.text.strip().lower().replace("%", "_pct")
        for th in table.find("thead").find("tr").find_all("th")
    ]
    headers.insert(0, "ottoneu_player_id")
    rows = list()
    for tr in table.find("tbody").find_all("tr"):
        row = list()
        for i, td in enumerate(tr.find_all("td")):
            if i == 0:
                row.append(int(td.find("a")["href"].rsplit("/", maxsplit=1)[1]))
            row.append(td.text.strip())
        rows.append(row)

    return pd.DataFrame(data=rows, columns=headers)


def summary(prob, df: pd.DataFrame):
    # clean this up
    div = "---------------------------------------\n"
    print("Variables:\n")
    score = str(prob.objective)
    constraints = [str(const) for const in prob.constraints.values()]
    for v in prob.variables():
        score = score.replace(v.name, str(v.varValue))
        constraints = [const.replace(v.name, str(v.varValue)) for const in constraints]
        if v.varValue != 0:
            print(v.name, "=", v.varValue)
    print(div)
    print("Constraints:")
    for constraint in constraints:
        constraint_pretty = " + ".join(re.findall("[0-9\.]*\*1.0", constraint))
        if constraint_pretty != "":
            print("{} = {}".format(constraint_pretty, eval(constraint_pretty)))
    print(div)
    print("Score:")
    score_pretty = " + ".join(re.findall("[0-9\.]+\*1.0", score))
    print("{} = {}".format(score_pretty, eval(score)))


def main():
    # set as env var? argparse?
    save = False
    yesterday = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
    df = get_sixpicks_leaderboard(yesterday)
    mappings = get_name_map()
    df = df.merge(
        mappings[["ottoneu_player_id", "ottoneu_position"]],
        on="ottoneu_player_id",
        how="left",
    )
    df["price"] = df.price.str.replace("$", "").astype(float)
    df["pts"] = df.pts.astype(float)
    df["ottoneu_position"] = df.ottoneu_position.fillna("")
    df["G"] = df.ottoneu_position.apply(lambda val: 1 if "G" in val else 0)
    df["F"] = df.ottoneu_position.apply(lambda val: 1 if "F" in val else 0)
    df["C"] = df.ottoneu_position.apply(lambda val: 1 if "C" in val else 0)
    salaries = dict()
    points = dict()
    positions = ["G", "F", "C"]
    for pos in positions:
        # filter df to elig players
        pos_df = df.loc[df[pos] == 1]
        salary = list(
            pos_df[["ottoneu_player_id", "price"]]
            .set_index("ottoneu_player_id")
            .to_dict()
            .values()
        )[0]
        point = list(
            pos_df[["ottoneu_player_id", "pts"]]
            .set_index("ottoneu_player_id")
            .to_dict()
            .values()
        )[0]
        salaries[pos] = salary
        points[pos] = point

    pos_num_available = {
        "G": {"min": 1, "max": 3},
        "F": {"min": 1, "max": 3},
        "C": {"min": 1, "max": 3},
    }

    _vars = {k: LpVariable.dict(k, v, cat="Binary") for k, v in points.items()}
    prob = LpProblem("Fantasy", LpMaximize)

    rewards = []
    costs = []
    # Setting up the reward
    for k, v in _vars.items():
        costs += lpSum([salaries[k][i] * _vars[k][i] for i in v])
        rewards += lpSum([points[k][i] * _vars[k][i] for i in v])
        prob += lpSum([_vars[k][i] for i in v]) <= pos_num_available[k]["max"]
        prob += lpSum([_vars[k][i] for i in v]) >= pos_num_available[k]["min"]

    # get list of player IDs
    for pid in df.ottoneu_player_id.unique():
        relevant_vars = list()
        # iterate through positions
        for pos, players in _vars.items():
            if pid in players.keys():
                relevant_vars.append(players[pid])
        prob += lpSum(relevant_vars) <= 1, f"unique_player_{pid}"

    prob += lpSum(_vars) == 6
    prob += lpSum(rewards)
    prob += lpSum(costs) <= SALARY_CAP

    result = prob.solve(PULP_CBC_CMD(msg=False))
    if save:
        summary(prob, df)
    else:
        player_ids = [
            int(v.name.rsplit("_")[1]) for v in prob.variables() if v.varValue != 0
        ]
        df.loc[df.ottoneu_player_id.isin(player_ids)].to_csv(sys.stdout, index=False)
        cleanup_and_save_images(player_ids, mappings)


if __name__ == "__main__":
    main()
