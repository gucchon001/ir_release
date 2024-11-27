# drive_handler.py
from utils.logging_config import get_logger
from pathlib import Path
from datetime import datetime
from googleapiclient.http import MediaIoBaseDownload

logger = get_logger(__name__)

class DriveHandler:
    def __init__(self, drive_uploader):
        self.drive_uploader = drive_uploader

    def save_summary_to_drive(self, folder_id, summary, file_name):
        """
        要約を Google Drive に保存します。一意のファイル名を生成するため、タイムスタンプを付与します。
        """
        # タイムスタンプを生成しファイル名に追加
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_file_name = f"{Path(file_name).stem}_{timestamp}{Path(file_name).suffix}"
        logger.info(f"要約を Google Drive に保存します。ファイル名: {unique_file_name}")

        # ファイルをアップロード
        file_id = self.drive_uploader.upload_file(
            file_name=unique_file_name,
            file_content=summary.encode("utf-8"),
            folder_id=folder_id,
            mime_type="text/markdown"
        )
        logger.info(f"要約を Google Drive に保存しました。ファイル ID: {file_id}")
        return file_id

    def download_pdf_from_drive(self, file_id: str) -> str:
        """
        Google Drive からPDFファイルをダウンロードする

        Args:
            file_id (str): ダウンロードするファイルの Google Drive ID

        Returns:
            str: ダウンロードしたファイルのローカルパス
        """
        try:
            # ファイルのメタデータを取得
            file_metadata = self.drive_uploader.drive_service.files().get(fileId=file_id).execute()
            file_name = file_metadata.get('name')
            
            # ダウンロード先のパスを設定
            download_dir = Path("downloads")
            download_dir.mkdir(exist_ok=True)
            local_path = download_dir / file_name

            # ファイルをダウンロード
            request = self.drive_uploader.drive_service.files().get_media(fileId=file_id)
            with open(local_path, 'wb') as f:
                downloader = MediaIoBaseDownload(f, request)
                done = False
                while done is False:
                    status, done = downloader.next_chunk()
                    if status:
                        logger.info(f"Download {int(status.progress() * 100)}%.")

            logger.info(f"ファイルをダウンロードしました: {local_path}")
            return str(local_path)

        except Exception as e:
            logger.error(f"ファイルのダウンロード中にエラーが発生しました: {e}")
            raise