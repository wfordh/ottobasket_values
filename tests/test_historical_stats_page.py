from streamlit.testing.v1 import AppTest


def test_historical_stats_page() -> None:
    at = AppTest.from_file("src/pages/historical_stats.py", default_timeout=10).run()
    assert not at.exception
    df = at.dataframe[0]
    assert df.type == "arrow_data_frame"
