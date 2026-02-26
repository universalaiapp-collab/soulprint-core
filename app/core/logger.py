import logging
from pythonjsonlogger import jsonlogger

def setup_logger():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    handler = logging.StreamHandler()

    formatter = jsonlogger.JsonFormatter(
        "%(asctime)s %(levelname)s %(message)s %(org_id)s %(path)s %(status_code)s"
    )

    handler.setFormatter(formatter)
    logger.addHandler(handler)
