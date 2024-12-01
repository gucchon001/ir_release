#operations.py
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import requests
from google.oauth2 import service_account
from googleapiclient.discovery import build
from utils.environment import EnvironmentUtils as env
from utils.logging_config import get_logger
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

# 名前付きロガーを取得
logger = get_logger(__name__)

class EDINETOperations:
    """EDINET API操作クラス"""

    TARGET_DOC_TYPES: Dict[str, str] = {
        '120': '有価証券報告書',
        '140': '四半期報告書',
        '160': '半期報告書'
    }

    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None, 
                 parent_folder_id: Optional[str] = None, service_account_file: Optional[str] = None, 
                 max_workers: int = 10):
        """
        EDINETOperations クラスの初期化
        """
        logger.info("EDINET Operations を初期化中...")

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
                raise ValueError(f"必要な設定値が不足しています: {', '.join(missing_config)}")
            
            logger.debug("設定値を正常にロードしました。")

        except Exception as e:
            logger.error(f"EDINETOperations の初期化に失敗しました: {e}")
            raise

        # Google Drive APIを初期化
        self.drive_service = None
        self.initialize_drive_service()

        # ThreadPoolExecutorの最大スレッド数
        self.max_workers = max_workers

    def initialize_drive_service(self):
        """Google Drive APIサービスの初期化"""
        try:
            credentials = service_account.Credentials.from_service_account_file(
                str(self.service_account_file),
                scopes=['https://www.googleapis.com/auth/drive.file']
            )
            self.drive_service = build('drive', 'v3', credentials=credentials)
            logger.info("Google Drive サービスを正常に初期化しました。")
        except Exception as e:
            logger.error(f"Drive サービスの初期化に失敗しました: {e}")
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
        dates = [(start_date + timedelta(days=day_offset)).strftime('%Y-%m-%d') for day_offset in range(total_days)]

        logger.info(f"{total_days} 日分のドキュメントを並列で取得開始します。")

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_date = {executor.submit(self.fetch_documents_for_date, date, edinet_codes_from_sheet): date for date in dates}
            for future in as_completed(future_to_date):
                date = future_to_date[future]
                try:
                    daily_documents = future.result()
                    documents.extend(daily_documents)
                    logger.debug(f"{date} のドキュメントを {len(daily_documents)} 件取得しました。")
                except Exception as e:
                    logger.error(f"{date} のドキュメント取得中に例外が発生しました: {e}")

        logger.info(f"指定期間内に取得した総ドキュメント数: {len(documents)}")
        return documents

    def fetch_documents_for_date(self, target_date: str, edinet_codes_from_sheet: List[str]) -> List[Dict]:
        """
        指定日のEDINET文書を取得

        Args:
            target_date (str): 対象日 (YYYY-MM-DD)
            edinet_codes_from_sheet (List[str]): スプレッドシートから取得したEDINETコードリスト

        Returns:
            List[Dict]: フィルタリングされた文書情報のリスト
        """
        filtered_results = []
        logger.debug(f"{target_date} のドキュメントを取得中...")

        try:
            url = f"{self.base_url}/documents.json"
            params = {
                "date": target_date,
                "type": "2",
                "Subscription-Key": self.api_key
            }
            response = requests.get(url, params=params, timeout=10)

            if response.status_code != 200:
                logger.warning(f"{target_date} のレスポンスが成功ではありませんでした: {response.text}")
                return []

            data = response.json()
            results = data.get('results', [])

            # フィルタリング対象のEDINETコードのみ取得
            filtered_results = [
                doc for doc in results
                if (doc.get('edinetCode') in edinet_codes_from_sheet and
                    doc.get('docTypeCode') in self.TARGET_DOC_TYPES and
                    doc.get('pdfFlag') == '1')
            ]

            logger.info(f"{target_date} のフィルタリング結果数: {len(filtered_results)}")
            return filtered_results

        except requests.exceptions.RequestException as e:
            logger.error(f"{target_date} のドキュメント取得に失敗しました: {e}")
            return []
        except Exception as e:
            logger.error(f"{target_date} の処理中に予期しないエラーが発生しました: {e}")
            return []

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

        logger.debug(f"doc_id {doc_id} のPDFドキュメントをリクエスト中...")

        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            # PDFフォーマットチェック
            if not response.content.startswith(b'%PDF-'):
                logger.error(f"doc_id {doc_id} のPDFフォーマットが無効です。")
                return None

            logger.debug(f"doc_id {doc_id} のPDFドキュメントを正常に取得しました。サイズ: {len(response.content)} バイト")
            return response.content
        except requests.exceptions.RequestException as e:
            logger.error(f"doc_id {doc_id} のドキュメント取得に失敗しました: {e}")
            return None
