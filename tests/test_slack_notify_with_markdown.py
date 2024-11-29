import sys
from pathlib import Path

# プロジェクトのルートディレクトリを計算して Python パスに追加
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))
sys.path.append(str(project_root / "src"))  # src ディレクトリも追加

from modules.slack.slack_notify import SlackNotifier
from modules.slack.drive_handler import DriveHandler
from utils.logging_config import get_logger


logger = get_logger(__name__)

def test_slack_notification_with_markdown(slack_channel: str, file_id: str, env_path: str = "config/secrets.env"):
    try:
        notifier = SlackNotifier(env_path=env_path)
        drive_handler = DriveHandler(notifier.service_account_file)
        content = drive_handler.get_file_content(file_id)
        notifier.send_formatted_markdown(slack_channel, content)
    except Exception as e:
        logger.error(f"Slack通知中にエラーが発生しました: {e}")
        raise

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python test_slack_notify_with_markdown.py [channel] [file_id]")
        sys.exit(1)
    
    test_slack_notification_with_markdown(sys.argv[1], sys.argv[2])