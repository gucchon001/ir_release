# src/modules/pdfSummary/process_drive_file.py

from .pdf_main import process_pdf
from utils.environment import EnvironmentUtils as env
from utils.drive_handler import DriveHandler
from utils.logging_config import get_logger

logger = get_logger(__name__)

def process_drive_file(file_id: str, drive_folder_id: str) -> list:
    """
    Google DriveのPDFファイルを処理して要約を生成し、ファイルIDのリストを返す

    Args:
        file_id (str): 処理対象のPDFファイルのGoogle Drive ID
        drive_folder_id (str): 保存先フォルダのGoogle Drive ID

    Returns:
        list: 要約ファイルのGoogle DriveファイルIDのリスト
    """
    try:
        # サービスアカウントファイルの取得
        service_account_file = env.get_service_account_file()
        drive_handler = DriveHandler(str(service_account_file))

        # PDFファイルをダウンロードして処理
        local_pdf_path = drive_handler.download_pdf_from_drive(file_id)
        if local_pdf_path:
            # PDFの処理
            result = process_pdf(local_pdf_path, drive_folder_id, drive_handler)
            if result:
                logger.info(f"処理が完了しました。結果のファイルID: {result}")
                return result
            else:
                logger.error("PDFの処理に失敗しました")
                return []
        else:
            logger.error("PDFのダウンロードに失敗しました")
            return []
    except Exception as e:
        logger.error(f"エラーが発生しました: {e}")
        return []
