import os
import logging
from dotenv import load_dotenv  # dotenvを使用
from typing import Optional
from openai import OpenAI
from utils import read_file_safely, write_file_content
from icecream import ic  # Icecream デバッグ用

# ロガーの設定
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

# .envファイルを読み込む
load_dotenv(dotenv_path="config/secrets.env")  # .envファイルのパスを指定

class SpecificationGenerator:
    """仕様書生成を管理するクラス"""

    def __init__(self):
        """設定を読み込んで初期化"""
        try:
            # APIキーを.envファイルから読み取る
            self.api_key = os.getenv('OPENAI_API_KEY')
            ic(self.api_key)  # デバッグ: APIキーを確認
            if not self.api_key:
                raise ValueError("OpenAI APIキーが設定されていません。config/secrets.env を確認してください。")

            # 固定値の設定
            self.model = "gpt-4o"
            self.temperature = 0.7

            # ディレクトリ設定
            self.source_dir = os.path.abspath(".")
            self.document_dir = os.path.join(self.source_dir, 'docs')
            self.prompt_file = os.path.join(self.source_dir, 'spec_tools', 'prompt_generate_detailed_spec.txt')
            ic(self.source_dir, self.document_dir, self.prompt_file)  # デバッグ: パスを確認

            # OpenAIクライアントを初期化
            self.client = OpenAI(api_key=self.api_key)

            logger.debug(f"SpecificationGenerator initialized with model: {self.model}")
        except Exception as e:
            logger.error(f"SpecificationGeneratorの初期化に失敗しました: {e}")
            raise

    def generate(self) -> str:
        """仕様書を生成してファイルに保存"""
        try:
            # merge.txtの内容を読み込む
            code_content = self._read_merge_file()
            ic(code_content)  # デバッグ: merge.txtの内容を確認
            if not code_content:
                logger.error("コード内容が空です。")
                return ""

            # プロンプトファイルを読み込む
            prompt = self._read_prompt_file()
            ic(prompt)  # デバッグ: プロンプト内容を確認
            if not prompt:
                logger.error("プロンプトファイルの読み込みに失敗しました。")
                return ""

            # プロンプトの最終形を作成
            full_prompt = f"{prompt}\n\nコード:\n{code_content}"
            ic(full_prompt)  # デバッグ: 完成したプロンプトを確認

            # AI応答を取得
            specification = self._get_ai_response(full_prompt)
            ic(specification)  # デバッグ: 生成された仕様書を確認
            if not specification:
                return ""

            # 出力ファイルのパスを設定
            output_path = os.path.join(self.document_dir, 'detail_spec.txt')
            ic(output_path)  # デバッグ: 出力パスを確認
            if write_file_content(output_path, specification):
                logger.info(f"仕様書が正常に出力されました: {output_path}")
                return output_path
            return ""
        except Exception as e:
            logger.error(f"仕様書生成中にエラーが発生しました: {e}")
            return ""

    def _read_merge_file(self) -> str:
        """merge.txt ファイルの内容を読み込む"""
        merge_path = os.path.join(self.document_dir, 'merge.txt')
        ic(merge_path)  # デバッグ: merge.txtのパスを確認
        content = read_file_safely(merge_path)
        if content:
            logger.info("merge.txt の読み込みに成功しました。")
        else:
            logger.error("merge.txt の読み込みに失敗しました。")
        return content or ""

    def _read_prompt_file(self) -> str:
        """プロンプトファイルを読み込む"""
        ic(self.prompt_file)  # デバッグ: プロンプトファイルのパスを確認
        try:
            with open(self.prompt_file, 'r', encoding='utf-8') as f:
                content = f.read()
                logger.info("prompt_generate_detailed_spec.txt の読み込みに成功しました。")
                return content
        except FileNotFoundError:
            logger.error(f"プロンプトファイルが見つかりません: {self.prompt_file}")
        except UnicodeDecodeError as e:
            logger.error(f"エンコードエラー: {e}")
        except Exception as e:
            logger.error(f"プロンプトファイルの読み込み中にエラーが発生しました: {e}")
        return ""

    def _get_ai_response(self, prompt: str) -> str:
        """OpenAI APIを使用して仕様書を生成"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "あなたは仕様書を作成するAIです。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature
            )
            logger.info("AI応答の取得に成功しました。")
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"AI応答取得中にエラーが発生しました: {e}")
            return ""

def generate_specification() -> str:
    """generate_specification 関数"""
    generator = SpecificationGenerator()
    return generator.generate()

if __name__ == "__main__":
    generate_specification()
