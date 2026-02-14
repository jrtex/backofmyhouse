import json
import logging
import sys
import traceback
from datetime import datetime, timezone


# Standard LogRecord attributes to exclude from extra fields
_LOG_RECORD_ATTRS = {
    "name", "msg", "args", "created", "relativeCreated", "exc_info",
    "exc_text", "stack_info", "lineno", "funcName", "pathname", "filename",
    "module", "thread", "threadName", "process", "processName", "levelname",
    "levelno", "message", "msecs", "taskName",
}


class JsonFormatter(logging.Formatter):
    """Formats log records as single-line JSON objects."""

    def format(self, record: logging.LogRecord) -> str:
        record.message = record.getMessage()

        log_data = {
            "timestamp": datetime.fromtimestamp(
                record.created, tz=timezone.utc
            ).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.message,
        }

        # Include extra fields added via logger.info("msg", extra={...})
        for key, value in record.__dict__.items():
            if key not in _LOG_RECORD_ATTRS and not key.startswith("_"):
                log_data[key] = value

        if record.exc_info and record.exc_info[0] is not None:
            log_data["exception"] = "".join(
                traceback.format_exception(*record.exc_info)
            )

        return json.dumps(log_data, default=str)


class TextFormatter(logging.Formatter):
    """Human-readable formatter for local development."""

    def format(self, record: logging.LogRecord) -> str:
        record.message = record.getMessage()
        timestamp = datetime.fromtimestamp(
            record.created, tz=timezone.utc
        ).strftime("%Y-%m-%d %H:%M:%S")

        parts = [
            f"{timestamp} [{record.levelname}] {record.name}: {record.message}"
        ]

        # Append extra fields
        for key, value in record.__dict__.items():
            if key not in _LOG_RECORD_ATTRS and not key.startswith("_"):
                parts.append(f"{key}={value}")

        output = " | ".join(parts)

        if record.exc_info and record.exc_info[0] is not None:
            output += "\n" + "".join(
                traceback.format_exception(*record.exc_info)
            )

        return output


def setup_logging(log_level: str = "INFO", log_format: str = "json") -> None:
    """Configure application-wide logging.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        log_format: Output format - "json" for structured or "text" for readable.
    """
    root_logger = logging.getLogger()

    # Prevent duplicate handlers on repeated calls
    if root_logger.handlers:
        root_logger.handlers.clear()

    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    # Stdout handler
    handler = logging.StreamHandler(sys.stdout)
    if log_format == "text":
        handler.setFormatter(TextFormatter())
    else:
        handler.setFormatter(JsonFormatter())
    root_logger.addHandler(handler)

    # Route uvicorn loggers through root (remove their default handlers)
    for logger_name in ("uvicorn", "uvicorn.access"):
        uv_logger = logging.getLogger(logger_name)
        uv_logger.handlers.clear()
        uv_logger.propagate = True

    # Suppress noisy third-party loggers
    for logger_name in ("httpx", "httpcore"):
        logging.getLogger(logger_name).setLevel(logging.WARNING)
