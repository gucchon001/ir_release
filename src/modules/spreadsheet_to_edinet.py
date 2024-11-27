from datetime import datetime

from utils.environment import EnvironmentUtils as env
from utils.spreadsheet import SpreadsheetService
from utils.drive_uploader import DriveUploader
from modules.edinet.operations import EDINETOperations
from utils.logging_config import get_logger

# 名前付きロガーを取得
logger = get_logger(__name__)


def log_download_to_sheet(spreadsheet_service, spreadsheet_id, log_sheet_name, log_data):
    """
    ダウンロードしたデータをログシートに記録する。
    ヘッダーを動的に取得し、列を特定して操作する。
    """
    try:
        sheet_data = spreadsheet_service.get_sheet_data(spreadsheet_id, log_sheet_name)

        if not sheet_data:
            logger.info(f"Log sheet '{log_sheet_name}' is empty. Initializing headers.")
            # デフォルトのヘッダーを使用して初期化
            default_headers = [
                'Release_Date',
                'EDINET_code',
                'stock_code',
                'corp_name',
                'doc_type',
                'drive_raw_data_file_name',
                'drive_raw_data_file_url',
                'timestamp'
            ]
            spreadsheet_service.update_sheet_data(
                spreadsheet_id, log_sheet_name, [default_headers]
            )
            sheet_data = [default_headers]

        # ヘッダー行を取得
        headers = sheet_data[0]
        logger.info(f"Retrieved headers: {headers}")

        # データ行を追加
        logger.info(f"Appending log data to sheet '{log_sheet_name}'.")
        spreadsheet_service.append_sheet_data(
            spreadsheet_id, log_sheet_name, log_data
        )
        logger.info("Log data appended successfully.")
    except Exception as e:
        logger.error(f"Failed to append log data to sheet '{log_sheet_name}': {e}")
        raise


def process_spreadsheet_data(config):
    """
    スプレッドシートデータを基に EDINET API を呼び出し、結果を Google Drive に直接保存。
    結果を log シートに記録。
    """
    try:
        # 環境変数と設定ファイルのロード
        env.load_env()

        # サービス初期化
        spreadsheet_service = SpreadsheetService()
        uploader = DriveUploader()

        # スプレッドシートIDとログシート名を取得
        spreadsheet_id = spreadsheet_service.get_spreadsheet_id("SPREADSHEET", "ss_id_list")
        log_sheet_name = "log"

        # 日付範囲を取得
        start_date = datetime.strptime(
            env.get_config_value("DATE_RANGE", "start_date"), "%Y-%m-%d"
        )
        end_date = datetime.strptime(
            env.get_config_value("DATE_RANGE", "end_date"), "%Y-%m-%d"
        )
        logger.info(f"Using date range from settings: {start_date} to {end_date}")

        # list シートのデータを取得
        list_data = spreadsheet_service.get_sheet_data(spreadsheet_id, "list")
        if not list_data:
            logger.error("No data found in the 'list' sheet.")
            return

        headers = list_data[0]
        data_rows = list_data[1:]
        if "EDINET_code" not in headers:
            logger.error("'EDINET_code' column not found in the 'list' sheet.")
            return
        edinet_code_index = headers.index("EDINET_code")

        edinet_operations = EDINETOperations()

        for row_index, row in enumerate(data_rows, start=2):
            edinet_code = row[edinet_code_index]
            stock_code = row[headers.index("stock_code")] if "stock_code" in headers else ""
            corp_name = row[headers.index("corp_name")] if "corp_name" in headers else ""
            logger.info(f"Processing row {row_index}: EDINET_code = {edinet_code}")

            try:
                documents = edinet_operations.get_documents_for_date_range(
                    start_date, end_date, [edinet_code]
                )

                for document in documents:
                    doc_id = document.get("docID")
                    doc_type_code = document.get("docTypeCode")
                    release_date = document.get("submitDateTime").split(" ")[0]
                    doc_type_name = EDINETOperations.TARGET_DOC_TYPES.get(doc_type_code, "不明")

                    # ファイル名生成
                    file_name = f"{edinet_code}_{doc_id}_{release_date.replace('-', '')}.pdf"

                    # フォルダの取得または作成
                    folder_id = uploader.get_or_create_folder(
                        folder_name=edinet_code,
                        parent_folder_id=env.get_config_value("DRIVE", "parent_folder_id")
                    )

                    # ドキュメントデータを取得
                    doc_data = edinet_operations.fetch_document_data(doc_id, doc_type_code)

                    if doc_data:
                        # Google Drive にアップロード
                        file_id = uploader.upload_file(
                            file_name=file_name,
                            file_content=doc_data,
                            folder_id=folder_id
                        )

                        # ログデータの作成と記録
                        file_url = f"https://drive.google.com/file/d/{file_id}/view"
                        log_data = [
                            [
                                release_date,
                                edinet_code,
                                stock_code,
                                corp_name,
                                doc_type_name,
                                file_name,
                                file_url,
                                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            ]
                        ]
                        log_download_to_sheet(
                            spreadsheet_service, spreadsheet_id, log_sheet_name, log_data
                        )
                        logger.info(f"File uploaded to Drive with URL: {file_url}")
                    else:
                        logger.warning(f"Failed to fetch document data: ID={doc_id}")

            except Exception as e:
                logger.error(f"Error processing EDINET_code {edinet_code}: {e}")
    except Exception as e:
        logger.error(f"Failed to process spreadsheet data: {e}")
        raise
