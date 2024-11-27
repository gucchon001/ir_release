import sys
from pathlib import Path

# プロジェクトのルートディレクトリを計算して Python パスに追加
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))
sys.path.append(str(project_root / "src"))  # src ディレクトリも追加

from modules.slack.slack_notify import test_slack_notification_with_file

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Test sending a Slack notification with a file link.")
    parser.add_argument("slack_channel", help="The Slack channel to send the notification.")
    parser.add_argument("message", help="The message to send to the Slack channel.")
    parser.add_argument("file_id", help="The Google Drive file ID to share.")
    parser.add_argument("--env_path", default="config/secrets.env", help="Path to the .env file (default: config/secrets.env).")
    args = parser.parse_args()

    try:
        test_slack_notification_with_file(args.slack_channel, args.message, args.file_id, args.env_path)
    except Exception as e:
        print(f"エラーが発生しました: {e}")
