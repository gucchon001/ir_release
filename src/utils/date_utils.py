from datetime import datetime, timedelta

def parse_date_string(date_str: str) -> datetime:
    """
    日付文字列を解析して datetime オブジェクトを返す。
    "yesterday" が指定された場合は前日の日付を返す。
    """
    if date_str.lower() == "yesterday":
        return datetime.now() - timedelta(days=1)
    return datetime.strptime(date_str, "%Y-%m-%d")
