from datetime import datetime, timedelta
from typing import Dict, List, Optional
import requests
from google.oauth2 import service_account
from googleapiclient.discovery import build
from utils.environment import EnvironmentUtils as env
from utils.logging_config import get_logger
import os

# 名前付きロガーを取得
logger = get_logger(__name__)

class EDINETOperations:
    """EDINET API操作クラス"""

    TARGET_DOC_TYPES: Dict[str, str] = {
        '120': '有価証券報告書',
        '140': '四半期報告書',
        '160': '半期報告書'
    }

    def __init__(self, base_url=None, api_key=None, parent_folder_id=None, service_account_file=None):
        """
        EDINETOperations クラスの初期化
        """
        logger.info("Initializing EDINET Operations...")

        # 環境変数をロード
        env.load_env()

        # 必要な設定をEnvironmentUtilsから取得
        try:
            self.base_url = base_url or env.get_config_value("EDINET", "base_url")
            self.api_key = api_key or os.getenv("EDINET_API_KEY")  # 環境変数から取得
            self.parent_folder_id = parent_folder_id or env.get_config_value("DRIVE", "parent_folder_id")
            self.service_account_file = service_account_file or env.get_service_account_file()

            # 設定値が不足している場合にエラーをスロー
            missing_config = []
            if not self.base_url:
                missing_config.append("base_url")
            if not self.api_key:
                missing_config.append("api_key")
            if not self.service_account_file:
                missing_config.append("service_account_file")

            if missing_config:
                raise ValueError(f"Missing required configuration values: {', '.join(missing_config)}")
            
            logger.debug(f"Config settings: base_url={self.base_url}, api_key=***, parent_folder_id={self.parent_folder_id}")

        except Exception as e:
            logger.error(f"Failed to initialize EDINETOperations: {e}")
            raise

        # Google Drive APIを初期化
        self.drive_service = None
        self.initialize_drive_service()

    def initialize_drive_service(self):
        """Google Drive APIサービスの初期化"""
        try:
            credentials = service_account.Credentials.from_service_account_file(
                str(self.service_account_file),
                scopes=['https://www.googleapis.com/auth/drive.file']
            )
            self.drive_service = build('drive', 'v3', credentials=credentials)
            logger.info("Google Drive service initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize Drive service: {e}")
            self.drive_service = None

    def get_documents_for_date_range(self, start_date: datetime, end_date: datetime, edinet_codes_from_sheet: List[str]) -> List[Dict]:
        """
        指定期間のEDINET文書を取得

        Args:
            start_date (datetime): 開始日
            end_date (datetime): 終了日
            edinet_codes_from_sheet (List[str]): スプレッドシートから取得したEDINETコードリスト

        Returns:
            List[Dict]: 文書情報のリスト
        """
        documents = []
        total_days = (end_date - start_date).days + 1

        for day_offset in range(total_days):
            target_date = (start_date + timedelta(days=day_offset)).strftime('%Y-%m-%d')
            logger.debug(f"Fetching documents for date: {target_date}")

            try:
                url = f"{self.base_url}/documents.json"
                params = {
                    "date": target_date,
                    "type": "2",
                    "Subscription-Key": self.api_key
                }
                response = requests.get(url, params=params)

                if response.status_code != 200:
                    logger.warning(f"Non-successful response for date {target_date}: {response.text}")
                    continue

                data = response.json()
                results = data.get('results', [])

                # フィルタリング対象のEDINETコードのみ取得
                filtered_results = [
                    doc for doc in results
                    if (doc.get('edinetCode') in edinet_codes_from_sheet and
                        doc.get('docTypeCode') in self.TARGET_DOC_TYPES and
                        doc.get('pdfFlag') == '1')
                ]

                logger.info(f"Filtered results count for {target_date}: {len(filtered_results)}")
                documents.extend(filtered_results)

            except Exception as e:
                logger.error(f"Failed to fetch documents for date {target_date}: {e}")

        logger.info(f"Total documents retrieved for date range: {len(documents)}")
        return documents

    def fetch_document_data(self, doc_id: str, doc_type_code: str) -> Optional[bytes]:
        """
        EDINET APIからPDFデータを取得

        Args:
            doc_id (str): ドキュメントID
            doc_type_code (str): ドキュメントタイプコード

        Returns:
            Optional[bytes]: PDFデータ、またはNone
        """
        url = f"{self.base_url}/documents/{doc_id}"
        params = {
            "type": "2",  # PDFデータ形式を指定
            "Subscription-Key": self.api_key,
        }

        logger.info(f"Requesting PDF document. URL: {url}, Params: {params}")

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()

            # PDFフォーマットチェック
            if not response.content.startswith(b'%PDF-'):
                logger.error(f"Invalid PDF format for doc_id {doc_id}.")
                return None

            logger.info(f"Successfully fetched PDF document for doc_id {doc_id}. Size: {len(response.content)} bytes")
            return response.content
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch document for doc_id {doc_id}: {e}")
            return None
