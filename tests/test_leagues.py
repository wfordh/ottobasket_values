import os
import sys

sys.path.append(os.path.abspath("src"))

import leagues  # type: ignore


def test_get_average_values():
    avg_vals = leagues.get_average_values()
    expected_cols = [
        "ottoneu_player_id",
        "name",
        "avg_salary",
        "median_salary",
        "roster%",
    ]

    actual_cols = avg_vals.columns.tolist()

    assert avg_vals.size > 0
    assert all([col in actual_cols for col in expected_cols])


test_get_average_values()
