import json

import gspread  # type: ignore
import pandas as pd


def _setup_gdrive(client_key_string: str) -> gspread.client.Client:
    credentials = json.loads(client_key_string)
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
