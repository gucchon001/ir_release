# spreadsheet_to_edinet.py

from datetime import datetime
from utils.environment import EnvironmentUtils as env
from utils.spreadsheet import SpreadsheetService
from modules.edinet.operations import EDINETOperations
from modules.pdfSummary.process_drive_file import process_drive_file
from utils.drive_handler import DriveHandler
from utils.date_utils import parse_date_string
from modules.slack.slack_notify import SlackNotifier

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
                'drive_summary_file_urls',  # 新しいカラムを追加
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
    結果を log シートに記録し、要約を Slack に通知。
    """
    try:
        # 環境変数と設定ファイルのロード
        env.load_env()

        # サービス初期化
        spreadsheet_service = SpreadsheetService()

        # スプレッドシートIDとログシート名を取得
        spreadsheet_id = spreadsheet_service.get_spreadsheet_id("SPREADSHEET", "ss_id_list")
        log_sheet_name = "log"

        # 日付範囲を取得
        try:
            start_date = parse_date_string(env.get_config_value("DATE_RANGE", "start_date"))
            end_date = parse_date_string(env.get_config_value("DATE_RANGE", "end_date"))
            logger.info(f"Using date range from settings: {start_date} to {end_date}")
        except ValueError as e:
            logger.error(f"Invalid date range configuration: {e}")
            raise

        # SlackNotifier の初期化
        slack_notifier = SlackNotifier(env_path="config/secrets.env")
        # Slack チャンネル名を設定ファイルから取得
        slack_channel = env.get_config_value("SLACK", "channel_id")

        # list シートのデータを取得
        list_data = spreadsheet_service.get_sheet_data(spreadsheet_id, "list")
        if not list_data:
            logger.error("No data found in the 'list' sheet.")
            return

        headers = list_data[0]
        data_rows = list_data[1:]
        if "EDINET_code" not in headers or "ir_page_url" not in headers or "check" not in headers:
            logger.error("'EDINET_code', 'ir_page_url', or 'check' column not found in the 'list' sheet.")
            return

        # 必要な列のインデックスを取得
        edinet_code_index = headers.index("EDINET_code")
        ir_page_url_index = headers.index("ir_page_url")
        check_index = headers.index("check")

        edinet_operations = EDINETOperations()

        # DriveHandler の初期化
        service_account_file = env.get_service_account_file()
        drive_handler = DriveHandler(str(service_account_file))

        for row_index, row in enumerate(data_rows, start=2):
            # `check`列がTRUEでない場合はスキップ
            check_value = row[check_index] if check_index < len(row) else "FALSE"
            if check_value.upper() != "TRUE":
                logger.info(f"Skipping row {row_index}: check value is not TRUE.")
                continue

            # 必要なデータを取得
            edinet_code = row[edinet_code_index]
            stock_code = row[headers.index("stock_code")] if "stock_code" in headers else ""
            corp_name = row[headers.index("corp_name")] if "corp_name" in headers else ""
            ir_page_url = row[ir_page_url_index] if ir_page_url_index < len(row) else ""

            logger.info(f"Processing row {row_index}: EDINET_code = {edinet_code}")

            if not ir_page_url:
                logger.warning(f"No IR page URL found for EDINET_code {edinet_code}.")
                continue

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
                    folder_id = drive_handler.get_or_create_folder(
                        folder_name=edinet_code,
                        parent_folder_id=env.get_config_value("DRIVE", "parent_folder_id")
                    )

                    # ドキュメントデータを取得
                    doc_data = edinet_operations.fetch_document_data(doc_id, doc_type_code)

                    if doc_data:
                        # Google Drive にアップロード
                        file_id = drive_handler.upload_file(
                            file_name=file_name,
                            file_content=doc_data,
                            folder_id=folder_id
                        )

                        # PDFを要約してGoogle Driveに保存
                        try:
                            summary_file_ids = process_drive_file(file_id, folder_id)
                            summary_urls = [
                                f"https://drive.google.com/file/d/{fid}/view" for fid in summary_file_ids
                            ]
                        except Exception as e:
                            logger.error(f"Failed to summarize PDF: {e}")
                            summary_file_ids = []
                            summary_urls = []

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
                                ", ".join(summary_urls),
                                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            ]
                        ]
                        log_download_to_sheet(
                            spreadsheet_service, spreadsheet_id, log_sheet_name, log_data
                        )
                        logger.info(f"File uploaded to Drive with URL: {file_url}")

                        # Slack通知の処理を追加
                        if summary_file_ids:
                            for summary_file_id in summary_file_ids:
                                try:
                                    markdown_content = drive_handler.get_file_content(summary_file_id)
                                    slack_notifier.send_formatted_markdown(
                                        slack_channel, markdown_content, ir_page_url
                                    )
                                    logger.info(f"Slackに要約を送信しました。ファイル ID: {summary_file_id}")
                                except Exception as e:
                                    logger.error(f"Slack通知中にエラーが発生しました（ファイル ID: {summary_file_id}）: {e}")
                        else:
                            logger.warning("要約ファイルがないため、Slack通知は行いませんでした。")

                    else:
                        logger.warning(f"Failed to fetch document data: ID={doc_id}")

            except Exception as e:
                logger.error(f"Error processing EDINET_code {edinet_code}: {e}")
    except Exception as e:
        logger.error(f"Failed to process spreadsheet data: {e}")
        raise