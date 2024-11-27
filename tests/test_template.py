import sys
from pathlib import Path
import os
from icecream import ic
from configparser import ConfigParser

# プロジェクトのルートディレクトリを計算し、`src` を `sys.path` に追加
project_root = Path(__file__).resolve().parent.parent  # ir_news_release ディレクトリ
src_path = project_root / "src"  # src ディレクトリ
sys.path.insert(0, str(src_path))  # sys.path の先頭に追加

from utils.logging_config import get_logger

# 設定ファイルのパス
CONFIG_PATH = project_root / "config/settings.ini"
ENV_PATH = project_root / "config/secrets.env"

def load_environment_variables(env_path):
    """
    secrets.env ファイルから環境変数を読み込む
    """
    if not env_path.exists():
        raise FileNotFoundError(f"Environment file not found: {env_path}")
    
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):  # 空行やコメントをスキップ
                continue
            key, value = line.split("=", 1)
            os.environ[key] = value
    ic(f"Environment variables loaded from {env_path}")

def sample_function():
    """
    サンプル関数：Hello TOMONOKAI を出力し、ログとデバッグ出力を行う
    """
    # ロガー初期化
    logger = get_logger()
    logger.info("Starting sample function")

    # 設定ファイルの読み込み
    config = ConfigParser()
    if CONFIG_PATH.exists():
        config.read(CONFIG_PATH)
        ic(f"Configuration loaded: {CONFIG_PATH}")
    else:
        logger.error(f"Configuration file not found: {CONFIG_PATH}")

    # secrets.env の読み込み
    try:
        load_environment_variables(ENV_PATH)
        logger.info(f"Environment variables loaded successfully from {ENV_PATH}")
    except FileNotFoundError as e:
        logger.error(str(e))
        return

    # サンプル出力
    api_key = os.getenv("EDINET_API_KEY", "未設定")
    logger.info(f"EDINET_API_KEY: {api_key}")
    ic(f"EDINET_API_KEY: {api_key}")

    print("Hello TOMONOKAI")
    logger.info("Sample function completed successfully.")

if __name__ == "__main__":
    sample_function()
