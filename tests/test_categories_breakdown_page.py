from streamlit.testing.v1 import AppTest


def test_categories_breakdown_page() -> None:
    at = AppTest.from_file(
        "src/pages/categories_breakdown.py", default_timeout=10
    ).run()
    assert not at.exception
    df = at.dataframe[0]
    assert df.type == "arrow_data_frame"
