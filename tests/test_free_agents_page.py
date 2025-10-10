from streamlit.testing.v1 import AppTest


def test_free_agents_page() -> None:
    at = AppTest.from_file("src/pages/free_agents.py", default_timeout=10).run()
    assert not at.exception
    df = at.dataframe[0]
    assert df.type == "arrow_data_frame"
