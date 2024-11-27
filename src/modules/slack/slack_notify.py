from pathlib import Path
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from googleapiclient.errors import HttpError
from utils.logging_config import get_logger
from .drive_handler import DriveHandler
import os

logger = get_logger(__name__)

class SlackNotifier:
    def __init__(self, env_path: str = "config/secrets.env"):
        # 環境変数のロード
        dotenv_path = Path(env_path)
        if not dotenv_path.exists():
            raise FileNotFoundError(f".env ファイルが見つかりません: {env_path}")
        from dotenv import load_dotenv
        load_dotenv(dotenv_path)
        logger.info(f".env ファイルをロードしました: {dotenv_path}")

        # Slack トークンを取得
        self.slack_token = os.getenv("SLACK_BOT_TOKEN")
        if not self.slack_token:
            raise ValueError("SLACK_BOT_TOKEN が設定されていません。secrets.env を確認してください。")
        logger.info("Slack トークンを正常に取得しました。")

        # Google Drive API 用のサービスアカウントファイルを取得
        self.service_account_file = os.getenv("SERVICE_ACCOUNT_FILE")
        if not self.service_account_file or not Path(self.service_account_file).exists():
            raise FileNotFoundError(f"SERVICE_ACCOUNT_FILE が設定されていないか、ファイルが見つかりません: {self.service_account_file}")
        logger.info(f"Google Drive サービスアカウントファイルをロードしました: {self.service_account_file}")

        # Slack クライアントを初期化
        self.client = WebClient(token=self.slack_token)

    def notify_with_file_content(self, channel: str, file_id: str):
        """
        Google Drive ファイルの内容を Slack に通知します。

        Args:
            channel (str): Slack チャネル ID または名前。
            file_id (str): Google Drive のファイル ID。
        """
        try:
            # Google Drive ファイル内容を取得
            drive_handler = DriveHandler(self.service_account_file)
            file_content = drive_handler.get_file_content(file_id)

            logger.info(f"Slack にファイル内容を送信中: チャネル={channel}")
            response = self.client.chat_postMessage(channel=channel, text=f"ファイル内容:\n{file_content}")
            logger.info(f"Slack にファイル内容を送信しました: {response['message']['text']}")
        except HttpError as e:
            logger.error(f"Google Drive API エラー: {e}")
            raise
        except SlackApiError as e:
            logger.error(f"Slack通知エラー: {e.response['error']}")
            raise
        except Exception as e:
            logger.error(f"ファイル内容の通知中にエラーが発生しました: {e}")
            raise


    def send_message(self, channel: str, message: str):
        """
        Slack にメッセージを送信します。

        Args:
            channel (str): Slack チャネル ID または名前
            message (str): 通知メッセージ
        """
        try:
            logger.info(f"Slack に通知を送信中: チャネル={channel}, メッセージ={message}")
            response = self.client.chat_postMessage(channel=channel, text=message)
            logger.info(f"Slack通知に成功しました: {response['message']['text']}")
        except SlackApiError as e:
            logger.error(f"Slack通知エラー: {e.response['error']}")
            raise

    def send_file(self, channel: str, file_id: str, title: str = "Markdown File"):
        """
        Slack にファイルをアップロードして送信します。

        Args:
            channel (str): Slack チャネル ID または名前
            file_id (str): Google Drive のファイル ID
            title (str): ファイルのタイトル
        """
        try:
            # Google Drive ファイルリンクを生成
            file_url = f"https://drive.google.com/file/d/{file_id}/view"
            logger.info(f"Slack にファイルリンクを送信中: チャネル={channel}, ファイルID={file_id}")

            # メッセージ形式でリンクを送信
            response = self.client.chat_postMessage(
                channel=channel,
                text=f"{title} のリンクを共有します:\n<{file_url}>"
            )
            logger.info(f"Slack ファイルリンクの送信に成功しました: {response['message']['text']}")
        except SlackApiError as e:
            logger.error(f"Slack ファイルリンク送信エラー: {e.response['error']}")
            raise

def test_slack_notification_with_file(slack_channel: str, message: str, file_id: str, env_path: str = "config/secrets.env"):
    """
    Slack通知をテストする関数 (メッセージ + ファイルリンク)。

    Args:
        slack_channel (str): 通知を送る Slack チャネル
        message (str): 通知するメッセージ
        file_id (str): Google Drive のファイル ID
        env_path (str): .env ファイルのパス
    """
    try:
        logger.info(f"Slack通知をテスト中: チャネル={slack_channel}, メッセージ={message}, ファイルID={file_id}")
        notifier = SlackNotifier(env_path=env_path)
        notifier.send_message(slack_channel, message)
        notifier.send_file(slack_channel, file_id, title="要約ファイル")
        print(f"Slack通知とファイルリンクを送信しました: チャネル={slack_channel}, メッセージ={message}, ファイルID={file_id}")
    except Exception as e:
        print(f"Slack通知中にエラーが発生しました: {e}")
        logger.error(f"Slack通知中にエラーが発生しました: {e}")
