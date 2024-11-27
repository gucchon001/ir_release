import pymupdf
from utils.logging_config import get_logger  # 修正: 絶対パスを使用

logger = get_logger(__name__)

def extract_text_from_pdf(pdf_path):
    """
    PyMuPDF を使用してPDFからテキストを抽出します。

    Args:
        pdf_path (str): PDFファイルのパス。

    Returns:
        str: 抽出されたテキスト。
    """
    logger.info(f"PDF ファイルからテキストを抽出: {pdf_path}")
    text = ""
    try:
        doc = pymupdf.open(pdf_path)
        for page_num, page in enumerate(doc, start=1):
            page_text = page.get_text()
            if page_text:
                text += page_text + "\n\n"
            logger.debug(f"ページ {page_num}: テキスト抽出完了")
    except Exception as e:
        logger.error(f"PyMuPDF によるテキスト抽出に失敗しました: {e}")
        raise
    logger.info(f"抽出されたテキストの合計文字数: {len(text)}")
    return text
