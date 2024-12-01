# generate_spec.py
import os
import logging
from typing import Optional
from openai import OpenAI
from utils import read_file_safely, write_file_content
from icecream import ic  # Icecream デバッグ用
from dotenv import load_dotenv  # dotenvを使用
from pathlib import Path
import subprocess
from datetime import datetime

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
            if not self.api_key:
                raise ValueError("OpenAI APIキーが設定されていません。secrets.env を確認してください。")

            self.model = "gpt-4o"  # モデルを固定
            self.temperature = 0.7  # デフォルト値として設定
            
            # ソースディレクトリの設定
            self.source_dir = os.path.abspath(".")
            self.document_dir = os.path.join(self.source_dir, 'docs')
            self.spec_tools_dir = os.path.join(self.source_dir, 'spec_tools')
            self.prompt_file = os.path.join(self.spec_tools_dir, 'prompt_requirements_spec.txt')  # プロンプトファイルのパス
            ic(self.source_dir, self.document_dir, self.prompt_file)  # デバッグ: ディレクトリ設定を確認

            # OpenAIクライアントを初期化
            self.client = OpenAI(api_key=self.api_key)

            logger.debug(f"SpecificationGenerator initialized with model: {self.model}")
        except Exception as e:
            logger.error(f"SpecificationGeneratorの初期化に失敗しました: {e}")
            raise

    def generate(self) -> str:
        """仕様書を生成してファイルに保存"""
        try:
            code_content = self._read_merge_file()
            ic(code_content)  # デバッグ: merge.txtの内容を確認
            if not code_content:
                logger.error("コード内容が空です。")
                return ""

            prompt = self._read_prompt_file()
            ic(prompt)  # デバッグ: 生成されたプロンプトを確認
            if not prompt:
                logger.error("プロンプトファイルの読み込みに失敗しました。")
                return ""

            full_prompt = f"{prompt}\n\nコード:\n{code_content}"
            ic(full_prompt)  # デバッグ: 完成したプロンプトを確認

            specification = self._get_ai_response(full_prompt)
            ic(specification)  # デバッグ: 生成された仕様書を確認
            if not specification:
                return ""

            # 出力先をdocsフォルダに設定
            output_path = os.path.join(self.document_dir, 'requirements_spec.txt')
            ic(output_path)  # デバッグ: 出力パスを確認
            if write_file_content(output_path, specification):
                logger.info(f"仕様書が正常に出力されました: {output_path}")
                
                # README.md を更新する
                self.update_readme()
                
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
        """プロンプトファイル (prompt_requirements_spec.txt) を読み込む"""
        ic(self.prompt_file)  # デバッグ: プロンプトファイルのパスを確認
        try:
            with open(self.prompt_file, 'r', encoding='utf-8') as f:  # Shift-JISで読み取り
                content = f.read()
                logger.info("prompt_requirements_spec.txt の読み込みに成功しました。")
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

    def get_project_tree(self) -> str:
        """プロジェクトのフォルダ構成をツリー形式で取得"""
        try:
            logger.info("プロジェクトのフォルダ構成を取得中...")
            # 'tree' コマンドを使用してフォルダ構成を取得
            # Windows環境を想定しています。必要に応じてUnix系に変更してください。
            result = subprocess.run(['tree', '/F'], capture_output=True, text=True, check=True)
            project_tree = result.stdout
            logger.debug(f"取得したフォルダ構成:\n{project_tree}")
            return project_tree
        except FileNotFoundError:
            logger.error("tree コマンドが見つかりません。Windows環境で実行してください。")
            return "tree コマンドが利用できません。"
        except subprocess.CalledProcessError as e:
            logger.error(f"フォルダ構成の取得中にエラーが発生しました: {e}")
            return "フォルダ構成の取得に失敗しました。"
        except Exception as e:
            logger.error(f"予期せぬエラーが発生しました: {e}")
            return "フォルダ構成の取得中にエラーが発生しました。"

    def update_readme(self) -> None:
        """README.md を README_tmp.md のテンプレートを使用して更新する"""
        try:
            readme_tmp_path = os.path.join(self.spec_tools_dir, 'README_tmp.md')
            readme_path = os.path.join(self.source_dir, 'README.md')

            logger.info(f"README.md を更新するためにテンプレートを読み込みます: {readme_tmp_path}")

            # README_tmp.md の内容を読み込む
            template_content = read_file_safely(readme_tmp_path)
            if not template_content:
                logger.error(f"{readme_tmp_path} の読み込みに失敗しました。README.md は更新されませんでした。")
                return

            # [spec] プレースホルダーを requirements_spec.txt の内容で置換
            spec_path = os.path.join(self.document_dir, 'requirements_spec.txt')
            spec_content = read_file_safely(spec_path)
            if not spec_content:
                logger.error(f"{spec_path} の読み込みに失敗しました。README.md の [spec] プレースホルダーは置換されませんでした。")
                spec_content = "[仕様書の内容が取得できませんでした。]"
            updated_content = template_content.replace("[spec]", spec_content)

            # [tree] プレースホルダーを merge.txt の内容からツリー図を取得して置換
            merge_path = os.path.join(self.document_dir, 'merge.txt')
            merge_content = read_file_safely(merge_path)
            if not merge_content:
                logger.error(f"{merge_path} の読み込みに失敗しました。README.md の [tree] プレースホルダーは置換されませんでした。")
                tree_content = "[フォルダ構成の取得に失敗しました。]"
            else:
                # " # Merged Python Files" までの内容を抽出
                split_marker = "# Merged Python Files"
                if split_marker in merge_content:
                    tree_section = merge_content.split(split_marker)[0]
                else:
                    tree_section = merge_content  # マーカーがなければ全体を使用
                tree_content = tree_section.strip()
            updated_content = updated_content.replace("[tree]", f"```\n{tree_content}\n```")

            # README.md に書き込む
            if write_file_content(readme_path, updated_content):
                logger.info(f"README.md が正常に更新されました: {readme_path}")
            else:
                logger.error(f"README.md の更新に失敗しました: {readme_path}")

        except Exception as e:
            logger.error(f"README.md の更新中にエラーが発生しました: {e}")
            raise

def generate_specification() -> str:
    """generate_specification 関数"""
    generator = SpecificationGenerator()
    return generator.generate()

if __name__ == "__main__":
    generate_specification()
