import json
import logging
from datetime import UTC, datetime

from app.core.request_context import RequestIdFilter


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", None),
        }
        return json.dumps(log)


def setup_logging():
    handler = logging.StreamHandler()          # logs → stdout
    handler.addFilter(RequestIdFilter())
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers.clear()                       # drop uvicorn's default text handler
    root.addHandler(handler)
    root.setLevel(logging.INFO)
