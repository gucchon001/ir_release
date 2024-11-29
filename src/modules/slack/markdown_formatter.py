from typing import List, Dict
import re
from utils.logging_config import get_logger

logger = get_logger(__name__)

class MarkdownSlackFormatter:
    def format_content(self, markdown_content: str) -> Dict:
        company_name = markdown_content.split('(')[1].split(')')[0]
        sections = self._split_sections(markdown_content)
        
        return {
            "attachments": [
                {
                    "color": "#36a64f",
                    "pretext": None,
                    "mrkdwn_in": ["text", "fields", "title", "footer"],
                    "title": f"*{company_name}* の決算情報",
                    "text": self._format_summary(sections['header']),
                    "fallback": f"{company_name}の決算情報",
                    "fields": self._format_sections(sections['content']),
                    "footer": "📑 情報取得元：金融庁 EDINET / GPT4oを使用して要約しています"
                    # footer_iconを削除し、代わりに絵文字を使用
                }
            ]
        }

    def _format_sections(self, content_sections: List[str]) -> List[Dict]:
        fields = []
        for section in content_sections:
            matches = re.match(r'(\d+\.\s*)(.*)', section)
            if matches:
                title = matches.group(2).strip()
                content = '\n'.join(section.split('\n')[1:])
                
                fields.append({
                    "title": f"{self._get_section_icon(title)} {title}",
                    "value": self._format_content(title, content),
                    "short": False
                })
        return fields

    def _format_content(self, title: str, content: str) -> str:
        formatted_lines = []
        for line in content.split('\n'):
            line = line.strip()
            if line:
                if line.startswith('- '):
                    formatted_lines.append(f"✦ {line[2:]}")
                else:
                    formatted_lines.append(line)
        return '\n'.join(formatted_lines)

    def _format_summary(self, header: str) -> str:
        lines = header.split('\n')[1:]
        return '\n'.join(line.strip() for line in lines)

    def _get_section_icon(self, title: str) -> str:
        icons = {
            'セグメント成長': '📊',
            '新しいトピック': '🆕',
            '損益計算書': '💹',
            '市場や競争環境': '🏢'
        }
        return icons.get(next((k for k in icons.keys() if k in title), ''), '📌')

    def _split_sections(self, content: str) -> Dict[str, any]:
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