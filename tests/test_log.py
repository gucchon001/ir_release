import logging
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from datetime import datetime

def test_logging():
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / f"app_{datetime.now().strftime('%Y%m%d')}.log"

    logger = logging.getLogger("test_logger")
    logger.setLevel(logging.DEBUG)

    handler = TimedRotatingFileHandler(
        log_file,
        when='midnight',
        interval=1,
        backupCount=30,
        encoding='utf-8'
    )

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    logger.info("This is a test log message.")

if __name__ == "__main__":
    test_logging()
