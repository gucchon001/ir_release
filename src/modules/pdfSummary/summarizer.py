import tiktoken
from concurrent.futures import ThreadPoolExecutor
from utils.logging_config import get_logger

logger = get_logger(__name__)

class Summarizer:
    def __init__(self, client, model, max_summary_tokens, prompt_messages):
        self.client = client
        self.model = model
        self.max_summary_tokens = max_summary_tokens
        self.prompt_messages = prompt_messages
        self.encoding = tiktoken.encoding_for_model(model)  # tiktoken のエンコーディングを取得

    def summarize_chunk(self, chunk):
        """
        単一のチャンクを要約します。
        """
        logger.info("チャンクを要約します。")
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    *self.prompt_messages,  # プロンプトメッセージを適用
                    {"role": "user", "content": chunk}
                ],
                max_tokens=self.max_summary_tokens,
                temperature=0.7
            )
            summary = response.choices[0].message.content.strip()
            logger.debug(f"要約結果: {summary[:100]}...")
            return summary
        except Exception as e:
            logger.error(f"チャンクの要約に失敗しました: {e}")
            raise

    def summarize_text(self, chunks):
        """
        複数のチャンクをまとめて要約。
        """
        logger.info("複数チャンクをまとめて要約します。")
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    *self.prompt_messages,
                    {"role": "user", "content": "\n\n".join(chunks)}
                ],
                max_tokens=self.max_summary_tokens,
                temperature=0.7
            )
            summary = response.choices[0].message.content.strip()
            logger.info("要約完了。")
            return summary
        except Exception as e:
            logger.error(f"要約全体の処理に失敗しました: {e}")
            raise

    def _summarize_recursive(self, summaries):
        """
        部分要約が長すぎる場合、さらに分割して再要約します。
        """
        combined_summary = " ".join(summaries)
        token_count = len(self.encoding.encode(combined_summary))  # トークン数を計算

        if token_count <= self.max_summary_tokens:
            return self.summarize_chunk(combined_summary)  # トークン数内なら要約

        logger.info("再要約のため、要約をさらに分割します。")
        midpoint = len(summaries) // 2
        left_summary = self._summarize_recursive(summaries[:midpoint])
        right_summary = self._summarize_recursive(summaries[midpoint:])

        return self.summarize_chunk(f"{left_summary} {right_summary}")
