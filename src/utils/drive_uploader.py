# src/utils/drive_uploader.py
from pathlib import Path
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from io import BytesIO
from utils.environment import EnvironmentUtils as env
from utils.logging_config import get_logger

# 名前付きロガーを取得
logger = get_logger(__name__)

class DriveUploader:
    def __init__(self):
        """
        DriveUploaderクラスの初期化。Google Drive APIを利用するための認証を行う。
        """
        # 環境変数をロード（必要に応じてsecrets.envを読み込む）
        env.load_env()

        # サービスアカウントファイルのパスを取得
        try:
            service_account_path = env.get_service_account_file()
            logger.info(f"Resolved service account file path: {service_account_path}")
        except FileNotFoundError as e:
            logger.error(f"Service account file not found: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to resolve service account file: {e}")
            raise

        # Google Drive API用の認証情報をロード
        try:
            self.credentials = Credentials.from_service_account_file(
                str(service_account_path),
                scopes=[
                    'https://www.googleapis.com/auth/drive',  # より広い権限を付与
                    'https://www.googleapis.com/auth/drive.file'
                ]
            )
            self.drive_service = build("drive", "v3", credentials=self.credentials)
            logger.info("Google Drive APIの認証が正常に完了しました。")
        except Exception as e:
            logger.error(f"Google Drive API認証に失敗しました: {e}")
            raise

    def get_or_create_folder(self, folder_name, parent_folder_id=None):
        """
        Google Drive上で指定された名前のフォルダを取得、または新規作成する。

        Args:
            folder_name (str): フォルダ名。
            parent_folder_id (str, optional): 親フォルダのID。

        Returns:
            str: フォルダID。
        """
        # フォルダ検索クエリを構築
        query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
        if parent_folder_id:
            query += f" and '{parent_folder_id}' in parents"

        # フォルダを検索
        try:
            results = self.drive_service.files().list(
                q=query, spaces="drive", fields="files(id, name)", pageSize=1
            ).execute()
            files = results.get("files", [])
            if files:
                folder_id = files[0]["id"]
                logger.info(f"既存のフォルダを発見: '{folder_name}' (ID: {folder_id})")
                return folder_id

            # フォルダが存在しない場合は作成
            folder_metadata = {
                "name": folder_name,
                "mimeType": "application/vnd.google-apps.folder",
                "parents": [parent_folder_id] if parent_folder_id else [],
            }
            folder = self.drive_service.files().create(
                body=folder_metadata, fields="id"
            ).execute()
            folder_id = folder.get("id")
            logger.info(f"新規フォルダを作成: '{folder_name}' (ID: {folder_id})")
            return folder_id
        except Exception as e:
            logger.error(f"フォルダの取得または作成に失敗しました: {e}")
            raise

    def upload_file(self, file_name, file_content, folder_id, mime_type="application/pdf"):
        """
        Google Driveにファイルをアップロードする。
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
            results = self.drive_service.files().list(
                q=query, spaces="drive", fields="files(id, name)", pageSize=1
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
            media = MediaIoBaseUpload(BytesIO(file_content), mimetype=mime_type)
            uploaded_file = self.drive_service.files().create(
                body=file_metadata, media_body=media, fields="id"
            ).execute()
            file_id = uploaded_file.get("id")
            logger.info(f"ファイルをアップロード: '{file_name}' (フォルダID: {folder_id}, ファイルID: {file_id})")
            return file_id

        except Exception as e:
            logger.error(f"ファイルのアップロードに失敗しました: {e}")
            raise