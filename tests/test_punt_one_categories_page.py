from streamlit.testing.v1 import AppTest


def test_punt_one_categories_page() -> None:
    at = AppTest.from_file("src/pages/punt_one_categories.py", default_timeout=10).run()
    assert not at.exception
    df = at.dataframe[0]
    assert df.type == "dataframe"
