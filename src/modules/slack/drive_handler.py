from googleapiclient.discovery import build
from google.oauth2 import service_account
from pathlib import Path

class DriveHandler:
    def __init__(self, service_account_file: str):
        """
        Google Drive API のハンドラーを初期化します。

        Args:
            service_account_file (str): サービスアカウントのキー JSON ファイルのパス。
        """
        self.service_account_file = service_account_file
        self.credentials = service_account.Credentials.from_service_account_file(
            self.service_account_file, scopes=["https://www.googleapis.com/auth/drive.readonly"]
        )
        self.service = build("drive", "v3", credentials=self.credentials)

    def get_file_content(self, file_id: str) -> str:
        """
        Google Drive ファイルの内容を取得します。

        Args:
            file_id (str): Google Drive のファイル ID。

        Returns:
            str: ファイルの内容。
        """
        try:
            request = self.service.files().get_media(fileId=file_id)
            file_content = request.execute()
            return file_content.decode("utf-8")  # Markdown ファイルは通常 UTF-8 形式
        except Exception as e:
            raise RuntimeError(f"Google Drive ファイルの読み込み中にエラーが発生しました: {e}")
