import json
import logging
import io

import pytest

from app.logging_config import setup_logging, JsonFormatter, TextFormatter


@pytest.fixture(autouse=True)
def reset_logging():
    """Reset root logger after each test to avoid handler buildup."""
    yield
    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(logging.WARNING)


class TestJsonFormatter:
    def test_produces_valid_json(self):
        formatter = JsonFormatter()
        record = logging.LogRecord(
            name="app.test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="test message",
            args=None,
            exc_info=None,
        )
        output = formatter.format(record)
        parsed = json.loads(output)
        assert parsed["message"] == "test message"
        assert parsed["level"] == "INFO"
        assert parsed["logger"] == "app.test"
        assert "timestamp" in parsed

    def test_includes_extra_fields(self):
        formatter = JsonFormatter()
        record = logging.LogRecord(
            name="app.test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="request",
            args=None,
            exc_info=None,
        )
        record.method = "GET"
        record.path = "/api/health"
        output = formatter.format(record)
        parsed = json.loads(output)
        assert parsed["method"] == "GET"
        assert parsed["path"] == "/api/health"

    def test_includes_exception_info(self):
        formatter = JsonFormatter()
        try:
            raise ValueError("boom")
        except ValueError:
            import sys
            exc_info = sys.exc_info()

        record = logging.LogRecord(
            name="app.test",
            level=logging.ERROR,
            pathname="test.py",
            lineno=1,
            msg="error occurred",
            args=None,
            exc_info=exc_info,
        )
        output = formatter.format(record)
        parsed = json.loads(output)
        assert "exception" in parsed
        assert "ValueError: boom" in parsed["exception"]


class TestTextFormatter:
    def test_produces_readable_output(self):
        formatter = TextFormatter()
        record = logging.LogRecord(
            name="app.test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="test message",
            args=None,
            exc_info=None,
        )
        output = formatter.format(record)
        assert "INFO" in output
        assert "app.test" in output
        assert "test message" in output

    def test_includes_extra_fields(self):
        formatter = TextFormatter()
        record = logging.LogRecord(
            name="app.test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="request",
            args=None,
            exc_info=None,
        )
        record.method = "GET"
        record.status_code = 200
        output = formatter.format(record)
        assert "method=GET" in output
        assert "status_code=200" in output


class TestSetupLogging:
    def test_attaches_stream_handler(self):
        setup_logging(log_level="INFO", log_format="json")
        root = logging.getLogger()
        stream_handlers = [
            h for h in root.handlers if isinstance(h, logging.StreamHandler)
        ]
        assert len(stream_handlers) >= 1

    def test_json_format_uses_json_formatter(self):
        setup_logging(log_level="INFO", log_format="json")
        root = logging.getLogger()
        formatters = [type(h.formatter) for h in root.handlers]
        assert JsonFormatter in formatters

    def test_text_format_uses_text_formatter(self):
        setup_logging(log_level="INFO", log_format="text")
        root = logging.getLogger()
        formatters = [type(h.formatter) for h in root.handlers]
        assert TextFormatter in formatters

    def test_respects_log_level(self):
        setup_logging(log_level="DEBUG", log_format="json")
        root = logging.getLogger()
        assert root.level == logging.DEBUG

    def test_respects_warning_level(self):
        setup_logging(log_level="WARNING", log_format="json")
        root = logging.getLogger()
        assert root.level == logging.WARNING

    def test_suppresses_noisy_loggers(self):
        setup_logging(log_level="DEBUG", log_format="json")
        httpx_logger = logging.getLogger("httpx")
        httpcore_logger = logging.getLogger("httpcore")
        assert httpx_logger.level >= logging.WARNING
        assert httpcore_logger.level >= logging.WARNING

    def test_configures_uvicorn_loggers(self):
        setup_logging(log_level="INFO", log_format="json")
        uvicorn_logger = logging.getLogger("uvicorn")
        uvicorn_access_logger = logging.getLogger("uvicorn.access")
        assert uvicorn_logger.handlers == []
        assert uvicorn_logger.propagate is True
        assert uvicorn_access_logger.handlers == []
        assert uvicorn_access_logger.propagate is True

    def test_logger_outputs_json_to_stream(self):
        setup_logging(log_level="INFO", log_format="json")
        stream = io.StringIO()
        root = logging.getLogger()
        # Replace the stream on the handler for capture
        for handler in root.handlers:
            if isinstance(handler, logging.StreamHandler):
                handler.stream = stream
                break

        test_logger = logging.getLogger("app.test.output")
        test_logger.info("hello from test")

        output = stream.getvalue()
        assert output.strip()
        parsed = json.loads(output.strip())
        assert parsed["message"] == "hello from test"
        assert parsed["logger"] == "app.test.output"

    def test_does_not_duplicate_handlers_on_repeated_calls(self):
        setup_logging(log_level="INFO", log_format="json")
        setup_logging(log_level="INFO", log_format="json")
        root = logging.getLogger()
        stream_handlers = [
            h for h in root.handlers if isinstance(h, logging.StreamHandler)
        ]
        assert len(stream_handlers) == 1
