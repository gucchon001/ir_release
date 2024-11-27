from anytree import Node, RenderTree
import os
from typing import Optional
import logging
import utils
from icecream import ic
from datetime import datetime
import argparse
import fnmatch

# ロガー設定
log_filename = f"merge_files_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(log_filename, encoding="utf-8")
    ]
)
logger = logging.getLogger(__name__)

class PythonFileMerger:
    def __init__(self, settings_path: str = 'config/settings.ini'):
        """INI設定を読み込んでマージャーを初期化"""
        try:
            self.settings = utils.read_settings(settings_path)
            self.project_dir = os.path.abspath(self.settings['source_directory'])
            self.output_dir = os.path.join(self.project_dir, 'docs')
            self.output_filename = self.settings['output_file']

            ic(self.project_dir)
            ic(self.output_dir)
            ic(self.output_filename)
            
            if not os.path.exists(self.output_dir):
                os.makedirs(self.output_dir)

            # 除外ディレクトリとファイルパターン
            self.exclude_dirs = ['env', 'myenv', '__pycache__', 'spec_tools', 'logs', 'log']
            self.exclude_files = ['*.log']
            ic(self.exclude_dirs)
            ic(self.exclude_files)

            logger.info(f"Initialized with project_dir: {self.project_dir}")
        except Exception as e:
            logger.error(f"Failed to initialize PythonFileMerger: {str(e)}")
            raise

    def _generate_tree_structure_with_anytree(self, root_dir: str) -> str:
        """`anytree` を使用してディレクトリ構造を生成"""
        def add_nodes(parent_node, parent_path):
            try:
                for item in sorted(os.listdir(parent_path)):
                    item_path = os.path.join(parent_path, item)
                    # ディレクトリを除外条件に基づきチェック
                    if os.path.isdir(item_path):
                        if item not in self.exclude_dirs:
                            dir_node = Node(item, parent=parent_node)
                            add_nodes(dir_node, item_path)
                    # ファイルを除外条件に基づきチェック
                    elif not any(fnmatch.fnmatch(item, pattern) for pattern in self.exclude_files):
                        Node(item, parent=parent_node)
            except PermissionError:
                pass  # アクセス権限のないディレクトリをスキップ

        root_node = Node(os.path.basename(root_dir))
        add_nodes(root_node, root_dir)
        tree_str = "\n".join([f"{pre}{node.name}" for pre, _, node in RenderTree(root_node)])
        return tree_str

    def process(self) -> Optional[str]:
        """ファイルマージ処理を実行"""
        try:
            logger.info(f"Collecting Python files from {self.project_dir}...")
            python_files = utils.get_python_files(self.project_dir, self.exclude_dirs)

            if not python_files:
                logger.warning(f"No Python files found in {self.project_dir}")
                return None

            # `anytree` を使ってフォルダ構造を取得
            tree_structure = self._generate_tree_structure_with_anytree(self.project_dir)
            merged_content = f"{tree_structure}\n\n# Merged Python Files\n\n"

            # Pythonファイルの内容を結合
            for rel_path, filepath in sorted(python_files):
                content = utils.read_file_safely(filepath)
                if content is not None:
                    merged_content += f"\n{'='*80}\nFile: {rel_path}\n{'='*80}\n\n{content}\n"
                else:
                    logger.warning(f"Skipped file due to read error: {filepath}")

            # 結果を保存
            output_path = os.path.join(self.output_dir, self.output_filename)
            output_success = utils.write_file_content(output_path, merged_content)

            if output_success:
                logger.info(f"Successfully wrote merged content to {output_path}")
                return output_path
            else:
                logger.error(f"Failed to write merged content to {output_path}")
                return None
        except Exception as e:
            logger.error(f"Error during file merge operation: {e}")
            return None

def merge_py_files(settings_path: str = 'config/settings.ini') -> Optional[str]:
    """マージ処理のエントリーポイント"""
    try:
        logger.info("Starting Python files merge process")
        merger = PythonFileMerger(settings_path=settings_path)
        return merger.process()
    except Exception as e:
        logger.error(f"Error in merge operation: {e}")
        return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Merge Python files into a single output.")
    parser.add_argument("--settings", type=str, default="config/settings.ini", help="Path to the settings.ini file")
    args = parser.parse_args()

    try:
        print("Starting merge_files.py...")
        output_file = merge_py_files(settings_path=args.settings)
        if output_file:
            print(f"Merge completed successfully. Output saved to: {output_file}")
        else:
            print("Merge failed. Check logs for details.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
