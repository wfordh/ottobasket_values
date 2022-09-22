import os
import sys

import altair as alt
import pandas as pd

sys.path.append(os.path.abspath("src"))
from calc_stats import calc_categories_value, calc_fantasy_pts
from transform import get_scoring_minutes_combo, prep_stats_df
