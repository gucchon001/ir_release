#pdf_main.py
from openai import OpenAI
from pathlib import Path
import json

from utils.environment import EnvironmentUtils as env
from utils.drive_uploader import DriveUploader
from .extractor import extract_text_from_pdf
from .tokenizer import Tokenizer
from .summarizer import Summarizer
from .drive_handler import DriveHandler
from utils.logging_config import get_logger

logger = get_logger(__name__)

def load_prompt(file_path: str) -> list:
    """
    プロンプトファイルをロードする

    Args:
        file_path (str): プロンプトファイルのパス

    Returns:
        list: プロンプトメッセージのリスト
    """
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            prompt_data = json.load(file)
            return prompt_data["messages"]
    except Exception as e:
        logger.error(f"プロンプトのロード中にエラーが発生しました: {e}")
        raise

def process_pdf(pdf_path, folder_id, drive_uploader=None):
    """
    PDF を処理して要約を作成し、Google Drive に保存します。

    Args:
        pdf_path (str): PDF ファイルのパス。
        folder_id (str): 要約を保存する Google Drive フォルダの ID。
        drive_uploader (DriveUploader, optional): 既存のDriveUploaderインスタンス。

    Returns:
        list: Google Drive に保存された要約ファイルの ID のリスト。
    """
    logger.info(f"PDF 処理を開始: {pdf_path}")

    # 環境変数をロード
    try:
        env.load_env()
        logger.info("環境変数を正常にロードしました。")
    except Exception as e:
        logger.error(f"環境変数のロード中にエラーが発生しました: {e}")
        raise

    # 必要な情報をロード
    api_key = env.get_openai_api_key()
    model = env.get_openai_model()
    max_chunk_tokens = 2000  # 分割サイズ
    max_summary_tokens = 2000  # 要約トークン制限

    # プロンプトをロード
    prompt_path = env.get_config_value("OPENAI", "prompt_financial_report", default="config/prompt_financial_report.json")
    prompt_file_path = env.resolve_path(prompt_path)
    try:
        prompt_messages = load_prompt(prompt_file_path)
        logger.info("プロンプトを正常にロードしました。")
    except Exception as e:
        logger.error(f"プロンプトのロードに失敗しました: {e}")
        raise

    # 必要なインスタンスを生成
    client = OpenAI(api_key=api_key)
    tokenizer = Tokenizer(model, max_chunk_tokens)
    summarizer = Summarizer(client, model, max_summary_tokens, prompt_messages)

    # DriveHandlerのインスタンス生成（既存のDriveUploaderがあれば使用）
    if drive_uploader is None:
        drive_uploader = DriveUploader()
    drive_handler = DriveHandler(drive_uploader)

    # PDFからテキストを抽出
    try:
        text = extract_text_from_pdf(pdf_path)
        logger.debug(f"PDF テキスト抽出完了。最初の100文字: {text[:100]}...")
    except Exception as e:
        logger.error(f"PDF テキスト抽出中にエラーが発生しました: {e}")
        raise

    # テキストを分割し要約
    try:
        chunks = tokenizer.split_text_into_chunks(text)
        summary = summarizer.summarize_text(chunks)
        logger.debug(f"要約完了。最初の100文字: {summary[:100]}...")
    except Exception as e:
        logger.error(f"要約処理中にエラーが発生しました: {e}")
        raise

    # 要約をGoogle Driveに保存
    try:
        file_ids = []
        if len(summary) > 10000:  # 要約が長すぎる場合に分割保存
            parts = [summary[i:i+10000] for i in range(0, len(summary), 10000)]
            for idx, part in enumerate(parts):
                part_file_name = f"{Path(pdf_path).stem}_summary_part_{idx+1}.md"
                file_id = drive_handler.save_summary_to_drive(folder_id, part, part_file_name)
                file_ids.append(file_id)
                logger.info(f"分割要約をGoogle Drive に保存しました。ファイル ID: {file_id}")
        else:  # 通常保存
            file_name = Path(pdf_path).stem + "_summary.md"
            file_id = drive_handler.save_summary_to_drive(folder_id, summary, file_name)
            file_ids.append(file_id)
            logger.info(f"要約をGoogle Drive に保存しました。ファイル ID: {file_id}")
        return file_ids
    except Exception as e:
        logger.error(f"Google Drive に保存中にエラーが発生しました: {e}")
        raise

def test_process_drive_file(file_id: str, drive_folder_id: str):
    """
    Google DriveのPDFファイルを処理するテスト関数
    
    Args:
        file_id (str): 処理対象のPDFファイルのGoogle Drive ID
        drive_folder_id (str): 保存先フォルダのGoogle Drive ID
    """
    try:
        # DriveUploaderとDriveHandlerのインスタンス作成
        drive_uploader = DriveUploader()
        drive_handler = DriveHandler(drive_uploader)
        
        # PDFファイルをダウンロードして処理
        local_pdf_path = drive_handler.download_pdf_from_drive(file_id)
        if local_pdf_path:
            # PDFの処理 - 同じDriveUploaderインスタンスを渡す
            result = process_pdf(local_pdf_path, drive_folder_id, drive_uploader)
            
            if result:
                print(f"処理が完了しました。結果のファイルID: {result}")
            else:
                print("PDFの処理に失敗しました")
        else:
            print("PDFのダウンロードに失敗しました")
            
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        raise
