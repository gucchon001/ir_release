import os
from pathlib import Path
from typing import Optional
from utils.environment import EnvironmentUtils as env
from utils.logging_config import get_logger

# 名前付きロガーを取得
logger = get_logger(__name__)

class EDINETConfig:
    REQUIRED_KEYS = ['base_url', 'api_key', 'parent_folder_id']

    def __init__(self, environment: Optional[str] = None):
        """
        EDINETConfigの初期化

        Args:
            environment (Optional[str]): 環境名（デフォルトは現在の環境を自動取得）
        """
        self.environment = environment or env.get_environment()
        self.settings = {}

        logger.info(f"Initializing EDINETConfig for environment: {self.environment}")

        # .envファイルをロード
        self._load_env()

        # 設定の読み込みと検証
        self._load_settings()
        self._validate_settings()

    def _load_env(self):
        """
        環境変数をロードする
        """
        try:
            env.load_env()
            logger.info("Environment variables loaded successfully.")

            # デバッグ用：主要な環境変数を確認
            for key in ["EDINET_API_KEY", "SERVICE_ACCOUNT_FILE"]:
                logger.debug(f"{key}: {os.getenv(key)}")
        except FileNotFoundError as e:
            logger.error(f"Environment file not found: {e}")
            raise

    def _load_settings(self):
        """
        EnvironmentUtilsを利用して設定を読み込む
        """
        try:
            # 環境変数または設定ファイルから設定をロード
            self.settings['api_key'] = env.get_env_var("EDINET_API_KEY", default=env.get_config_value("EDINET", "api_key"))
            if not self.settings['api_key']:
                logger.warning("API key is missing. Please set 'EDINET_API_KEY' or define it in settings.ini.")

            self.settings['base_url'] = env.get_config_value('EDINET', 'base_url', default="https://disclosure.edinet-fsa.go.jp/api/v1")
            self.settings['parent_folder_id'] = env.get_config_value('DRIVE', 'parent_folder_id', default="")

            # サービスアカウントファイルをsecrets.envまたは設定ファイルから取得
            service_account_file = env.get_env_var("SERVICE_ACCOUNT_FILE", default=env.get_config_value("GOOGLE", "service_account_file"))
            if not service_account_file:
                raise ValueError("Service account file is missing. Please set 'SERVICE_ACCOUNT_FILE' in secrets.env or settings.ini.")

            self.settings['service_account_file'] = self._resolve_path(service_account_file)
            self.settings['download_dir'] = env.get_config_value('EDINET', 'download_dir', default="data/edinet")

            logger.info("Configuration settings loaded successfully.")
            logger.debug(f"Loaded settings: {self.settings}")
        except Exception as e:
            logger.error(f"Failed to load settings: {e}")
            raise

    def _validate_settings(self):
        """
        設定値の検証

        Raises:
            ValueError: 必須キーが欠落している場合
        """
        logger.info("Validating configuration settings...")
        missing_keys = [key for key in self.REQUIRED_KEYS if not self.settings.get(key)]
        if not self.settings.get('service_account_file'):
            missing_keys.append('service_account_file')

        if missing_keys:
            logger.error(f"Missing required configuration keys: {', '.join(missing_keys)}")
            raise ValueError(f"Missing required configuration keys: {', '.join(missing_keys)}")
        logger.info("All required settings are valid.")

    def _resolve_path(self, path: str) -> Path:
        """
        指定されたパスをプロジェクトルートに基づいて解決します。

        Args:
            path (str): 相対パスまたは絶対パス

        Returns:
            Path: 解決された絶対パス
        """
        resolved_path = Path(path)
        if not resolved_path.is_absolute():
            resolved_path = env.get_project_root() / resolved_path

        logger.debug(f"Resolving path: input={path}, resolved={resolved_path}")

        if not resolved_path.exists():
            logger.error(f"Resolved path does not exist: {resolved_path}")
            raise FileNotFoundError(f"Resolved path does not exist: {resolved_path}")

        return resolved_path

    @property
    def base_url(self) -> str:
        """
        EDINET APIのベースURLを取得
        """
        return self.settings.get('base_url')

    @property
    def api_key(self) -> str:
        """
        EDINET APIキーを取得
        """
        return self.settings.get('api_key')

    @property
    def parent_folder_id(self) -> str:
        """
        Google Driveの親フォルダIDを取得
        """
        return self.settings.get('parent_folder_id')

    @property
    def service_account_file(self) -> Path:
        """
        サービスアカウントファイルのパスを取得
        """
        return self.settings.get('service_account_file')

    def get_download_dir(self) -> Path:
        """
        ダウンロードディレクトリのパスを取得

        Returns:
            Path: ダウンロードディレクトリのパス
        """
        download_dir = Path(self.settings.get('download_dir'))
        if not download_dir.is_absolute():
            download_dir = env.get_project_root() / download_dir
        download_dir.mkdir(parents=True, exist_ok=True)
        return download_dir
