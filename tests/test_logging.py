# tests/test_logging.py

import unittest
import logging
import os
from pathlib import Path
from src.utils.logging_config import get_logger, LoggingConfig

class TestLogging(unittest.TestCase):
    def setUp(self):
        # LoggingConfig のシングルトンをリセット
        LoggingConfig._initialized = False

        # ログディレクトリとログファイルのパスを設定
        self.log_dir = Path("logs")
        self.log_dir.mkdir(exist_ok=True)
        
        # テスト用のログファイル名を設定
        self.log_file = self.log_dir / "test_logging.log"
        
        # 既存のログファイルがあれば削除
        if self.log_file.exists():
            os.remove(self.log_file)
        
        # ロガーの取得（テスト用のログファイルを指定し、log_level を DEBUG に設定、再初期化を許可）
        self.logger = get_logger("test_logging", log_file=self.log_file, log_level="DEBUG", reset=True)

    def tearDown(self):
        # ロギングをシャットダウンしてメッセージをフラッシュ
        logging.shutdown()

    def test_logging_levels(self):
        # 各ログレベルのメッセージをログに記録
        self.logger.debug("DEBUG メッセージ")
        self.logger.info("INFO メッセージ")
        self.logger.warning("WARNING メッセージ")
        self.logger.error("ERROR メッセージ")
        self.logger.critical("CRITICAL メッセージ")

        # ロギングをシャットダウンしてメッセージをフラッシュ
        logging.shutdown()

        # ログファイルの存在確認
        self.assertTrue(self.log_file.exists(), "ログファイルが作成されていません。")

        # ログファイルの内容を確認
        with open(self.log_file, "r", encoding="utf-8") as f:
            logs = f.read()
            self.assertIn("DEBUG メッセージ", logs)
            self.assertIn("INFO メッセージ", logs)
            self.assertIn("WARNING メッセージ", logs)
            self.assertIn("ERROR メッセージ", logs)
            self.assertIn("CRITICAL メッセージ", logs)

    def test_icecream_enabled(self):
        # IceCreamの有効化を確認するテスト
        try:
            from icecream import ic
            self.logger.debug("IceCreamテスト")
            ic("IceCreamが有効です。")
            # 実際の出力をキャプチャする方法が必要
            # ここでは単純にエラーが発生しないことを確認
            self.assertTrue(True)
        except ImportError:
            self.fail("IceCreamがインポートできません。")

if __name__ == "__main__":
    unittest.main()
