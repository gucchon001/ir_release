from sentence_transformers import SentenceTransformer, util
import tiktoken
from utils.logging_config import get_logger

logger = get_logger(__name__)

class Tokenizer:
    def __init__(self, model, max_chunk_tokens):
        self.encoding = tiktoken.encoding_for_model(model)
        self.max_chunk_tokens = max_chunk_tokens
        self.sentence_model = SentenceTransformer('all-MiniLM-L6-v2')  # センテンスエンベディングモデル

    def count_tokens(self, text):
        """テキスト内のトークン数をカウントします。"""
        token_count = len(self.encoding.encode(text))
        logger.debug(f"トークン数: {token_count}")
        return token_count

    def split_text_into_chunks(self, text):
        """意味的に近いまとまりでテキストを分割します。"""
        logger.info("テキストを意味的に分割します。")

        # テキストを文単位に分割
        sentences = [sentence.strip() for sentence in text.split(".") if sentence.strip()]
        
        # 各文をエンコードしてセンテンスエンベディングを取得
        embeddings = self.sentence_model.encode(sentences, convert_to_tensor=True)

        # 意味的に近い文をグループ化する
        clusters = []
        current_cluster = []
        current_cluster_length = 0

        for i, sentence in enumerate(sentences):
            sentence_tokens = self.count_tokens(sentence)

            if current_cluster_length + sentence_tokens > self.max_chunk_tokens:
                clusters.append(" ".join(current_cluster))
                current_cluster = []
                current_cluster_length = 0

            current_cluster.append(sentence)
            current_cluster_length += sentence_tokens

        if current_cluster:
            clusters.append(" ".join(current_cluster))

        logger.info(f"分割されたチャンク数: {len(clusters)}")
        return clusters
