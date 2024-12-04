#main.py
from typing import Callable, Optional, Any
from datetime import datetime, timedelta

from modules.edinet.operations import EDINETOperations
from modules.edinet.config import EDINETConfig
from modules.spreadsheet_to_edinet import process_spreadsheet_data
from utils.spreadsheet import SpreadsheetService
from utils.environment import EnvironmentUtils as env
from utils.date_utils import parse_date_string
from utils.logging_config import get_logger

# 名前付きロガーを取得
logger = get_logger(__name__)

def run_process(process_func: Callable, config: Optional[Any] = None) -> None:
    """汎用プロセス実行関数"""
    try:
        logger.info(f"Starting process: {process_func.__name__}")
        process_func(config)
        logger.info(f"Process {process_func.__name__} completed successfully.")
    except Exception as e:
        logger.error(f"Error in {process_func.__name__}: {e}", exc_info=True)
        raise RuntimeError(f"Process {process_func.__name__} failed.") from e

def edinet_process(config: EDINETConfig) -> None:
    """
    EDINET API を使用して指定された期間内のドキュメントを取得
    """
    edinet = EDINETOperations(
        base_url=config.base_url,
        api_key=config.api_key,
        parent_folder_id=config.parent_folder_id,
        service_account_file=config.service_account_file,
    )

    start_date_str = env.get_config_value("DATE_RANGE", "start_date")
    end_date_str = env.get_config_value("DATE_RANGE", "end_date")

    if not start_date_str or not end_date_str:
        raise ValueError("DATE_RANGE section or required keys are missing in the settings.ini file.")

    # 動的な日付解析
    start_date = parse_date_string(start_date_str)
    end_date = parse_date_string(end_date_str)
    
    logger.debug(f"Fetching documents from {start_date} to {end_date}")

    spreadsheet_service = SpreadsheetService()
    spreadsheet_id = spreadsheet_service.get_spreadsheet_id("SPREADSHEET", "ss_id_list")
    list_data = spreadsheet_service.get_sheet_data(spreadsheet_id, "list")

    if not list_data or len(list_data) < 2:
        logger.error("Spreadsheet data is empty or invalid format.")
        raise ValueError("Spreadsheet data is empty or invalid format.")

    headers = list_data[0]
    data_rows = list_data[1:]
    edinet_code_index = headers.index("EDINET_code")
    edinet_codes_from_sheet = [row[edinet_code_index] for row in data_rows]

    logger.info(f"Edinet codes retrieved from spreadsheet.")

    documents = edinet.get_documents_for_date_range(
        start_date=start_date,
        end_date=end_date,
        edinet_codes_from_sheet=edinet_codes_from_sheet
    )

    logger.info(f"Total documents retrieved: {len(documents)}")
    for document in documents:
        logger.debug(f"Retrieved Document - ID: {document.get('docID')}, Description: {document.get('docDescription')}")

def main() -> None:
    """メイン処理"""
    try:
        # 環境変数のロード
        env.load_env()

        # 設定ファイルの取得
        config_path = env.get_config_file()
        logger.info(f"Config file located at: {config_path}")

        # EDINETの設定を初期化
        edinet_config = EDINETConfig()
        edinet_config.config_path = config_path

        logger.info(f"Current environment: {env.get_environment()}")

        # 各プロセスの実行
        run_process(edinet_process, edinet_config)
        run_process(process_spreadsheet_data, edinet_config)

    except Exception as e:
        logger.error(f"Fatal error in main execution: {e}", exc_info=True)

if __name__ == "__main__":
    main()
