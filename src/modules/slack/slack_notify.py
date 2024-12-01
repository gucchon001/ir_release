# slack_notifier.py
from pathlib import Path
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from utils.logging_config import get_logger
import os
import re
from typing import List, Dict, Optional
from dotenv import load_dotenv

logger = get_logger(__name__)

class MarkdownSlackFormatter:
    """
    Markdownテキストを Slack の Block Kit 形式にフォーマットするクラス。
    会社の決算情報を構造化された形式で表示し、インタラクティブな要素を提供します。
    """
    def format_content(self, markdown_content: str, ir_page_url: str) -> Dict:
        """
        Markdownコンテンツを Slack の Block Kit 形式に変換します。

        Args:
            markdown_content (str): 変換対象のMarkdownテキスト
            ir_page_url (str): IR情報ページへのURL

        Returns:
            Dict: Block Kit形式のメッセージ構造
        """
        # 会社名を抽出
        company_name = self._extract_company_name(markdown_content)
        
        # コンテンツをセクションに分割
        sections = self._split_sections(markdown_content)
        blocks = []

        # ヘッダーブロック（会社名）
        blocks.append(self._create_header_block(company_name))

        # 基本情報ブロック
        if sections['header']:
            blocks.append(self._create_section_block(
                self._format_summary(sections['header'])
            ))

        # セクション区切り
        blocks.append({"type": "divider"})

        # 各セクションのブロック
        for section in self._format_sections(sections['content']):
            blocks.append(self._create_section_block(
                f"*{section['title']}*\n{section['value']}"
            ))

        # フッター情報とボタン
        blocks.extend(self._create_footer_blocks(ir_page_url))

        return {"blocks": blocks}

    def _extract_company_name(self, markdown_content: str) -> str:
        """
        Markdownコンテンツから会社名を抽出します。
        前株式会社と後株式会社の両方のパターンに対応します。

        Args:
            markdown_content (str): 解析対象のMarkdownテキスト

        Returns:
            str: 抽出された会社名、見つからない場合は"不明な会社名"
        """
        try:
            # パターン1: 会社名欄での検索
            patterns = [
                r'会社名:\s*\*\*(株式会社[^*]+)\*\*',  # 前株式会社パターン
                r'会社名:\s*\*\*([^株]+株式会社)\*\*',  # 後株式会社パターン
                r'決算短信の要約\s*\(\*\*(株式会社[^*]+)\*\*\)',  # タイトルでの前株式会社
                r'決算短信の要約\s*\(\*\*([^株]+株式会社)\*\*\)'  # タイトルでの後株式会社
            ]
            
            for pattern in patterns:
                match = re.search(pattern, markdown_content)
                if match:
                    return match.group(1)
            
            return "不明な会社名"
            
        except Exception as e:
            logger.error(f"会社名の抽出中にエラーが発生しました: {str(e)}")
            return "不明な会社名"

    def _create_header_block(self, company_name: str) -> Dict:
        """ヘッダーブロックを作成します"""
        return {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"{company_name}の決算情報",
                "emoji": True
            }
        }

    def _create_section_block(self, text: str) -> Dict:
        """セクションブロックを作成します"""
        return {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": text
            }
        }

    def _create_footer_blocks(self, ir_page_url: str) -> List[Dict]:
        """フッター情報とボタンブロックを作成します"""
        return [
            {"type": "divider"},
            {
                "type": "context",
                "elements": [{
                    "type": "mrkdwn",
                    "text": "📊 金融庁 EDINET / GPT4oを使用して要約しています"
                }]
            },
            {
                "type": "actions",
                "elements": [{
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "📑 関連IR情報をもっと見る",
                        "emoji": True
                    },
                    "style": "primary",
                    "url": ir_page_url,
                    "action_id": "view_ir_info"
                }]
            }
        ]

    def _format_sections(self, content_sections: List[str]) -> List[Dict]:
        """セクションの内容をフォーマットします"""
        fields = []
        for section in content_sections:
            matches = re.match(r'(\d+\.\s*)(.*)', section)
            if matches:
                title = matches.group(2).strip()
                content = '\n'.join(section.split('\n')[1:])
                fields.append({
                    "title": f"{self._get_section_icon(title)} {title}",
                    "value": self._format_content_text(content),
                    "short": False
                })
        return fields

    def _format_content_text(self, content: str) -> str:
        """テキストコンテンツを整形します"""
        lines = []
        for line in content.split('\n'):
            line = line.strip()
            if line:
                if line.startswith('✦ '):
                    lines.append(line)
                elif line.startswith('- '):
                    lines.append(f"✦ {line[2:]}")
                else:
                    lines.append(line)
        return '\n'.join(lines)

    def _format_summary(self, header: str) -> str:
        """サマリー部分を整形します"""
        return '\n'.join(
            line.strip() for line in header.split('\n')[1:]
            if line.strip()
        )

    def _get_section_icon(self, title: str) -> str:
        """セクションに対応するアイコンを取得します"""
        icons = {
            'セグメント成長': '📊',
            '新しいトピック': '🆕',
            '損益計算書': '💹',
            '市場や競争環境': '🏢'
        }
        return icons.get(next((k for k in icons.keys() if k in title), ''), '📌')

    def _split_sections(self, content: str) -> Dict[str, any]:
        """コンテンツを各セクションに分割します"""
        parts = content.split('\n1.')
        header = parts[0].strip()
        content_sections = []

        if len(parts) > 1:
            remaining = '1.' + parts[1]
            current_section = []
            for line in remaining.split('\n'):
                if re.match(r'^\d+\.', line):
                    if current_section:
                        content_sections.append('\n'.join(current_section))
                    current_section = [line]
                else:
                    current_section.append(line)

            if current_section:
                content_sections.append('\n'.join(current_section))

        return {
            'header': header,
            'content': content_sections
        }

class SlackNotifier:
    """
    Slack通知を処理するクラス。
    環境設定の管理とメッセージの送信を担当します。
    """
    def __init__(self, env_path: str = "config/secrets.env"):
        # 環境変数の設定を読み込み
        self._load_environment(env_path)
        
        # Slackクライアントとフォーマッタを初期化
        self.client = WebClient(token=self.slack_token)
        self.formatter = MarkdownSlackFormatter()
        logger.info("Slack通知システムの初期化が完了しました")

    def _load_environment(self, env_path: str):
        """環境変数をロードします"""
        dotenv_path = Path(env_path)
        if not dotenv_path.exists():
            raise FileNotFoundError(f".env ファイルが見つかりません: {env_path}")
        
        load_dotenv(dotenv_path)
        
        self.slack_token = os.getenv("SLACK_BOT_TOKEN")
        if not self.slack_token:
            raise ValueError("SLACK_BOT_TOKEN が設定されていません")

        logger.info("環境設定のロードが完了しました")

    def send_formatted_markdown(self, channel: str, markdown_content: str, ir_page_url: str):
        """
        フォーマットされたMarkdownをSlackに送信します。
        ボットの表示名とアイコンをカスタマイズして送信を行います。

        Args:
            channel (str): 送信先のSlackチャンネルID
            markdown_content (str): 送信するMarkdown形式のコンテンツ
            ir_page_url (str): IR情報ページのURL
        """
        try:
            formatted_content = self.formatter.format_content(
                markdown_content, ir_page_url
            )
            
            # 基本のメッセージ内容にボットの表示設定を追加
            message_params = {
                **formatted_content,  # 既存のフォーマット済みコンテンツ
                "channel": channel,
                "username": "決算通知bot",  # ボットの表示名
                "icon_emoji": ":chart_with_upwards_trend:",  # 📈 グラフ上昇の絵文字
                # または画像URLを使用する場合：
                # "icon_url": "https://example.com/path/to/bot-icon.png"
            }
            
            response = self.client.chat_postMessage(**message_params)
            logger.info(f"Slack通知を送信しました: {response['ts']}")
                
        except SlackApiError as e:
            logger.error(f"Slack API エラー: {e.response['error']}")
            raise
        except Exception as e:
            logger.error(f"予期せぬエラーが発生しました: {e}")
            raise