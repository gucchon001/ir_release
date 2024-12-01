import os
from pathlib import Path
from configparser import ConfigParser
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

from utils.environment import EnvironmentUtils as env
from utils.logging_config import get_logger

class SpreadsheetService:
    """スプレッドシート操作を管理するクラス"""

    def __init__(self):
        """
        初期化メソッド。
        ログ設定とGoogle Sheets APIサービスの初期化を行います。
        """
        self.logger = get_logger(__name__)
        self.logger.info("Initializing SpreadsheetService...")

        # サービスアカウントファイルを取得
        try:
            # 環境変数または設定ファイルから取得
            service_account_file = os.getenv("SERVICE_ACCOUNT_FILE", "config/service_account.json")
            
            # パスを解決
            service_account_path = self._resolve_path(service_account_file)

            # Google 認証情報をロード
            if not service_account_path.exists():
                raise FileNotFoundError(f"Service account file not found: {service_account_path}")

            self.credentials = Credentials.from_service_account_file(str(service_account_path))
            self.logger.info("Service account file successfully loaded.")
        except Exception as e:
            self.logger.error(f"Failed to load service account file: {e}")
            raise

        # Google Sheets API サービスを初期化
        try:
            self.service = build("sheets", "v4", credentials=self.credentials)
            self.logger.info("Google Sheets API service initialized successfully.")
        except Exception as e:
            self.logger.error(f"Failed to initialize Google Sheets API service: {e}")
            raise

        # ConfigParser で設定ファイルをロード
        try:
            config_path = env.get_config_file()
            self.logger.info(f"Loading configuration from: {config_path}")
            self.config = ConfigParser()

            if not config_path.exists():
                raise FileNotFoundError(f"Configuration file not found: {config_path}")

            self.config.read(config_path, encoding='utf-8')  # エンコーディングを明示的に指定
        except Exception as e:
            self.logger.error(f"Error loading configuration: {e}")
            raise

    def _resolve_path(self, path: str) -> Path:
        """
        与えられたパスを絶対パスに解決します。

        :param path: 解決するパス
        :return: 絶対パス
        """
        resolved_path = Path(path)
        if not resolved_path.is_absolute():
            resolved_path = env.get_project_root() / resolved_path

        self.logger.debug(f"Resolved path: {resolved_path}")
        return resolved_path

    def get_sheet_data(self, spreadsheet_id: str, sheet_name: str):
        """
        指定されたスプレッドシートのデータを取得します。

        Args:
            spreadsheet_id (str): スプレッドシートID
            sheet_name (str): シート名

        Returns:
            List[List[str]]: スプレッドシートのデータ
        """
        self.logger.info(f"Fetching data from Spreadsheet ID: {spreadsheet_id}, Sheet Name: {sheet_name}")
        try:
            sheet = self.service.spreadsheets()
            result = sheet.values().get(spreadsheetId=spreadsheet_id, range=sheet_name).execute()
            data = result.get("values", [])
            self.logger.debug(f"Data fetched: {data}")
            return data
        except Exception as e:
            self.logger.error(f"Error fetching data for Sheet '{sheet_name}': {e}")
            raise

    def get_spreadsheet_id(self, section: str, option: str) -> str:
        """
        スプレッドシートIDを取得します。

        Args:
            section (str): 設定ファイルのセクション名
            option (str): 設定項目名

        Returns:
            str: スプレッドシートID
        """
        self.logger.info(f"Fetching Spreadsheet ID from section: {section}, option: {option}")
        try:
            if not self.config.has_section(section):
                raise ValueError(f"Section '{section}' not found in the configuration.")
            if not self.config.has_option(section, option):
                raise ValueError(f"Option '{option}' not found in section '{section}'.")
            spreadsheet_id = self.config.get(section, option)
            self.logger.debug(f"Spreadsheet ID retrieved: {spreadsheet_id}")
            return spreadsheet_id
        except Exception as e:
            self.logger.error(f"Error retrieving Spreadsheet ID: {e}")
            raise

    def append_sheet_data(self, spreadsheet_id: str, sheet_name: str, rows: list):
        """
        指定されたスプレッドシートのシートに行データを追加します。

        Args:
            spreadsheet_id (str): スプレッドシートID
            sheet_name (str): シート名
            rows (list): 追加する行データのリスト

        Returns:
            dict: APIのレスポンス
        """
        self.logger.info(f"Appending data to Spreadsheet ID: {spreadsheet_id}, Sheet Name: {sheet_name}")
        try:
            range_ = f"{sheet_name}!A1"
            body = {"values": rows}

            response = self.service.spreadsheets().values().append(
                spreadsheetId=spreadsheet_id,
                range=range_,
                valueInputOption="RAW",
                insertDataOption="INSERT_ROWS",
                body=body
            ).execute()

            self.logger.debug(f"Data appended successfully to Sheet: {sheet_name}, Response: {response}")
            return response
        except Exception as e:
            self.logger.error(f"Error appending data to sheet '{sheet_name}': {e}")
            raise
