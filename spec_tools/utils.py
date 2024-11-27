import os
import logging
import fnmatch
import configparser
from typing import List, Tuple, Optional

logger = logging.getLogger(__name__)

def normalize_path(path: str) -> str:
    """パスを正規化"""
    return os.path.normpath(path).replace('\\', '/')

def read_settings(settings_path: str = 'config/settings.ini') -> dict:
    """設定ファイルを読み込む"""
    config = configparser.ConfigParser()
    default_settings = {
        'source_directory': '.',  # デフォルトのソースディレクトリ
        'output_file': 'merge.txt',  # デフォルトの出力ファイル名
        'exclusions': 'myenv,*__pycache__*,sample_file,*.log',  # 除外パターン
        'openai_api_key': '',  # デフォルトのOpenAI APIキー
        'openai_model': 'gpt-4o'  # デフォルトのOpenAIモデル
    }
    
    try:
        if os.path.exists(settings_path):
            config.read(settings_path, encoding='utf-8')
            settings = {
                'source_directory': config['DEFAULT'].get('SourceDirectory', default_settings['source_directory']),
                'output_file': config['DEFAULT'].get('OutputFile', default_settings['output_file']),
                'exclusions': config['DEFAULT'].get('Exclusions', default_settings['exclusions']).replace(' ', '')
            }
            
            # APIセクションの設定を追加
            if 'API' in config:
                settings['openai_api_key'] = config['API'].get('openai_api_key', default_settings['openai_api_key'])
                settings['openai_model'] = config['API'].get('openai_model', default_settings['openai_model'])
            else:
                logger.warning("API section not found in settings.ini")
                settings['openai_api_key'] = default_settings['openai_api_key']
                settings['openai_model'] = default_settings['openai_model']
        else:
            logger.warning(f"Settings file not found at {settings_path}. Using default settings.")
            settings = default_settings

        # APIキーが設定されていない場合の警告
        if not settings['openai_api_key']:
            logger.warning("OpenAI API key is not set. Some functionality may be limited.")
        
        return settings
    except Exception as e:
        logger.error(f"Error reading settings file {settings_path}: {e}")
        return default_settings

def read_file_safely(filepath: str) -> Optional[str]:
    """ファイルを安全に読み込む"""
    for encoding in ['utf-8', 'cp932']:
        try:
            with open(filepath, 'r', encoding=encoding) as f:
                return f.read()
        except UnicodeDecodeError:
            continue  # 次のエンコーディングで試す
        except Exception as e:
            logger.error(f"Error reading file {filepath}: {e}")
            return None
    logger.warning(f"Failed to read file {filepath} with supported encodings.")
    return None

def write_file_content(filepath: str, content: str) -> bool:
    """ファイルに内容を書き込む"""
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    except Exception as e:
        logger.error(f"Error writing to file {filepath}: {e}")
        return False

def get_python_files(directory: str, exclude_patterns: List[str]) -> List[Tuple[str, str]]:
    """指定ディレクトリ配下のPythonファイルを取得"""
    python_files = []
    exclude_patterns = [pattern.strip() for pattern in exclude_patterns if pattern.strip()]  # パターンの正規化
    
    try:
        for root, dirs, files in os.walk(directory):
            # 除外パターンに一致するディレクトリをスキップ
            dirs[:] = [d for d in dirs if not any(fnmatch.fnmatch(d, pattern) for pattern in exclude_patterns)]
            
            for file in files:
                if file.endswith('.py') and not any(fnmatch.fnmatch(file, pattern) for pattern in exclude_patterns):
                    filepath = os.path.join(root, file)
                    rel_path = os.path.relpath(filepath, directory)
                    python_files.append((rel_path, filepath))
        
        return sorted(python_files)
    except Exception as e:
        logger.error(f"Error getting Python files from {directory}: {e}")
        return []
