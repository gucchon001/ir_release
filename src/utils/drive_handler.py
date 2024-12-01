# src/utils/drive_handler.py

import io
from googleapiclient.discovery import build
from google.oauth2 import service_account
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload
from pathlib import Path
from datetime import datetime

from utils.logging_config import get_logger

logger = get_logger(__name__)

class DriveHandler:
    def __init__(self, service_account_file: str):
        """
        Google Drive API のハンドラーを初期化します。

        Args:
            service_account_file (str): サービスアカウントのキー JSON ファイルのパス。
        """
        self.service_account_file = service_account_file
        try:
            self.credentials = service_account.Credentials.from_service_account_file(
                self.service_account_file,
                scopes=["https://www.googleapis.com/auth/drive"]
            )
            self.service = build("drive", "v3", credentials=self.credentials)
            logger.info("Google Drive API サービスが正常に初期化されました。")
        except Exception as e:
            logger.error(f"Google Drive API の初期化中にエラーが発生しました: {e}")
            raise

    def get_file_content(self, file_id: str) -> str:
        """
        指定されたGoogle Driveファイルの内容を取得します。

        Args:
            file_id (str): Google DriveのファイルID

        Returns:
            str: ファイルの内容
        """
        try:
            request = self.service.files().get_media(fileId=file_id)
            file_content = request.execute()
            content = file_content.decode("utf-8")  # Markdown ファイルは通常 UTF-8 形式
            logger.info(f"ファイル内容を取得しました。ファイルID: {file_id}")
            return content
        except Exception as e:
            logger.error(f"ファイル内容の取得中にエラーが発生しました。ファイルID: {file_id}, エラー: {e}")
            raise

    def save_summary_to_drive(self, folder_id: str, summary: str, file_name: str) -> str:
        """
        要約を Google Drive に保存します。一意のファイル名を生成するため、タイムスタンプを付与します。

        Args:
            folder_id (str): 保存先フォルダのID
            summary (str): 保存する要約内容
            file_name (str): 保存するファイル名

        Returns:
            str: 保存されたファイルのID
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_file_name = f"{Path(file_name).stem}_{timestamp}{Path(file_name).suffix}"
            logger.info(f"要約を Google Drive に保存します。ファイル名: {unique_file_name}")

            file_metadata = {
                "name": unique_file_name,
                "parents": [folder_id]
            }

            media = MediaIoBaseUpload(
                io.BytesIO(summary.encode("utf-8")),
                mimetype="text/markdown"
            )

            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields="id"
            ).execute()

            file_id = file.get("id")
            logger.info(f"要約を Google Drive に保存しました。ファイル ID: {file_id}")
            return file_id
        except Exception as e:
            logger.error(f"要約ファイルの保存中にエラーが発生しました: {e}")
            raise

    def download_pdf_from_drive(self, file_id: str) -> str:
        """
        Google Drive からPDFファイルをダウンロードします。

        Args:
            file_id (str): ダウンロードするファイルのGoogle Drive ID

        Returns:
            str: ダウンロードしたファイルのローカルパス
        """
        try:
            # ファイルのメタデータを取得
            file_metadata = self.service.files().get(fileId=file_id).execute()
            file_name = file_metadata.get('name')

            # ダウンロード先のパスを設定
            download_dir = Path("downloads")
            download_dir.mkdir(exist_ok=True)
            local_path = download_dir / file_name

            # ファイルをダウンロード
            request = self.service.files().get_media(fileId=file_id)
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()
                if status:
                    logger.debug(f"Download {int(status.progress() * 100)}%.")

            # ダウンロードした内容をローカルファイルに保存
            with open(local_path, 'wb') as f:
                f.write(fh.getvalue())

            logger.info(f"ファイルをダウンロードしました: {local_path}")
            return str(local_path)
        except Exception as e:
            logger.error(f"ファイルのダウンロード中にエラーが発生しました: {e}")
            raise

    def get_or_create_folder(self, folder_name: str, parent_folder_id: str = None) -> str:
        """
        指定された名前のフォルダを取得または作成します。

        Args:
            folder_name (str): フォルダ名。
            parent_folder_id (str, optional): 親フォルダのID。

        Returns:
            str: フォルダのID。
        """
        try:
            # フォルダ検索クエリを構築
            query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
            if parent_folder_id:
                query += f" and '{parent_folder_id}' in parents"

            # フォルダを検索
            results = self.service.files().list(
                q=query,
                spaces="drive",
                fields="files(id, name)",
                pageSize=1
            ).execute()
            files = results.get("files", [])

            if files:
                folder_id = files[0]["id"]
                logger.info(f"既存のフォルダを使用します。フォルダ名: '{folder_name}', フォルダID: {folder_id}")
                return folder_id
            else:
                # フォルダが存在しない場合は作成
                file_metadata = {
                    "name": folder_name,
                    "mimeType": "application/vnd.google-apps.folder",
                    "parents": [parent_folder_id] if parent_folder_id else [],
                }
                folder = self.service.files().create(
                    body=file_metadata,
                    fields="id"
                ).execute()
                folder_id = folder.get("id")
                logger.info(f"新規フォルダを作成しました。フォルダ名: '{folder_name}', フォルダID: {folder_id}")
                return folder_id
        except Exception as e:
            logger.error(f"フォルダの取得または作成中にエラーが発生しました: {e}")
            raise

    def upload_file(self, file_name: str, file_content: bytes, folder_id: str, mime_type: str = "application/pdf") -> str:
        """
        ファイルをGoogle Driveにアップロードします。
        既存の同名ファイルがある場合はスキップする。

        Args:
            file_name (str): アップロードするファイル名。
            file_content (bytes): アップロードするファイルの内容。
            folder_id (str): アップロード先のフォルダID。
            mime_type (str): ファイルのMIMEタイプ（デフォルトはPDF）。

        Returns:
            str: アップロードされたファイルのID。または既存のファイルのID。
        """
        try:
            # フォルダ内で同名ファイルを検索
            query = f"name='{file_name}' and '{folder_id}' in parents and trashed=false"
            results = self.service.files().list(
                q=query,
                spaces="drive",
                fields="files(id, name)",
                pageSize=1
            ).execute()
            existing_files = results.get("files", [])

            if existing_files:
                # 同名ファイルが存在する場合はスキップ
                file_id = existing_files[0]["id"]
                logger.info(f"同名ファイルが既に存在するためスキップ: '{file_name}' (フォルダID: {folder_id}, ファイルID: {file_id})")
                return file_id

            # ファイルのメタデータを設定
            file_metadata = {
                "name": file_name,
                "parents": [folder_id],
            }

            # ファイルをアップロード
            media = MediaIoBaseUpload(
                io.BytesIO(file_content),
                mimetype=mime_type
            )
            uploaded_file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields="id"
            ).execute()
            file_id = uploaded_file.get("id")
            logger.info(f"ファイルをアップロードしました: '{file_name}' (フォルダID: {folder_id}, ファイルID: {file_id})")
            return file_id
        except Exception as e:
            logger.error(f"ファイルのアップロードに失敗しました: {e}")
            raise
