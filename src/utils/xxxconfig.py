import os
import configparser
from pathlib import Path
import logging
from dotenv import load_dotenv
from typing import Any, Dict, Optional, Union
from icecream import ic

class BaseConfig:
    def __init__(self, env: str = 'development'):
        self.env = env
        self.logger = logging.getLogger(__name__)
        self.base_path = Path(__file__).parent.parent.parent

        # 環境変数と設定ファイルをロード
        self._load_env()
        self.config = self._load_config()
        self._settings: Dict[str, Any] = {}
        self._initialize_settings()

    def _load_env(self):
        """環境変数ファイルの読み込み"""
        env_path = self.base_path / 'config' / 'secrets.env'
        ic(f"Looking for env file at: {env_path}")

        if env_path.exists():
            load_dotenv(env_path)
            ic("Loaded secrets.env file from config directory")
        else:
            ic("secrets.env file not found in config directory")
            raise FileNotFoundError(f"{env_path} が見つかりません。環境変数を正しく設定してください。")

    def _load_config(self):
        """設定ファイルの読み込み"""
        config = configparser.ConfigParser()
        config_path = self.base_path / 'config' / 'settings.ini'
        ic(f"Config path resolved: {config_path}")

        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        try:
            with open(config_path, 'r', encoding='utf-8-sig') as f:
                config.read_file(f)
            ic(f"Loaded configuration from: {config_path} (UTF-8)")
        except UnicodeDecodeError:
            try:
                with open(config_path, 'r', encoding='cp932') as f:
                    config.read_file(f)
                ic(f"Loaded configuration using fallback encoding: {config_path} (Shift-JIS)")
            except Exception as e:
                ic(f"Failed to load configuration file: {e}")
                raise

        return config

    def get_service_account_file(self) -> Path:
        """
        環境変数 'SERVICE_ACCOUNT_FILE' を取得し、フルパスを返します。

        Returns:
            Path: サービスアカウントファイルのパス
        """
        service_account_file = os.getenv("SERVICE_ACCOUNT_FILE")
        if not service_account_file:
            raise ValueError("環境変数 'SERVICE_ACCOUNT_FILE' が設定されていません。")

        service_account_path = self.base_path / "config" / service_account_file
        if not service_account_path.exists():
            raise FileNotFoundError(f"サービスアカウントファイルが見つかりません: {service_account_path}")

        ic(f"Resolved service account file path: {service_account_path}")
        return service_account_path

    def get(self, key: str, default: Any = None) -> Any:
        """環境変数または設定値を取得します。"""
        value = os.getenv(key, self._settings.get(key, default))
        ic(f"Retrieved value for {key}: {value}")
        return value

class ServiceConfig(BaseConfig):
    """特定のサービス用設定クラス"""

    def __init__(self, service_name: str, env: str = 'development'):
        self.service_name = service_name.upper()
        ic(f"Initializing ServiceConfig for {self.service_name}")
        super().__init__(env=env)

    def _initialize_settings(self):
        """サービス固有の設定を初期化"""
        try:
            config_section = self.config[self.service_name]
            self._settings = self._parse_config_section(config_section)
            ic(f"{self.service_name} settings loaded: {self._settings}")
        except KeyError as e:
            ic(f"Missing section in configuration: {e}")
            raise

    def _parse_config_section(self, config_section: configparser.SectionProxy) -> Dict[str, Any]:
        """設定セクションをパースして適切な型に変換"""
        settings = {}
        for key, value in config_section.items():
            ic(f"Parsing key: {key}, value: {value}")
            # カンマ区切りの文字列をリストとして解釈
            if ',' in value:
                settings[key] = [v.strip() for v in value.split(',')]
                continue

            # 数値への変換を試行
            try:
                if value.isdigit():
                    settings[key] = int(value)
                elif value.replace('.', '', 1).isdigit():
                    settings[key] = float(value)
                else:
                    settings[key] = value
            except ValueError:
                settings[key] = value

        return settings
