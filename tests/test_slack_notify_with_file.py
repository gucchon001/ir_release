import sys
from pathlib import Path

# プロジェクトのルートディレクトリを計算して Python パスに追加
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))
sys.path.append(str(project_root / "src"))  # src ディレクトリも追加

from modules.slack.slack_notify import SlackNotifier

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Slack通知をテストするスクリプト。")
    parser.add_argument("slack_channel", help="Slackの通知先チャンネル名またはID。")
    parser.add_argument("file_id", help="Google Drive上のファイルID。")
    args = parser.parse_args()

    try:
        notifier = SlackNotifier(env_path="config/secrets.env")
        notifier.notify_with_file_content(args.slack_channel, args.file_id)
    except Exception as e:
        print(f"エラーが発生しました: {e}")
