import sys
from pathlib import Path

# プロジェクトのルートディレクトリをパスに追加
project_root = Path(__file__).resolve().parent.parent  # ir_news_release ディレクトリ
sys.path.append(str(project_root / "src"))

from utils.spreadsheet import SpreadsheetService
from icecream import ic

# 設定ファイルのパス
CONFIG_PATH = Path("config/settings.ini")

def test_list_sheet_headers():
    """list シートのヘッダ行を取得して確認"""
    service = SpreadsheetService(CONFIG_PATH)
    data = service.get_sheet_data("list")

    if data:
        ic(data[0])  # 最初の行を出力（ヘッダ行）
    else:
        print("No data found in 'list' sheet.")

if __name__ == "__main__":
    test_list_sheet_headers()
