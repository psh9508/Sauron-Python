import logging
from unittest.mock import patch, MagicMock

import sauron_python.sauron_sdk as sauron

EVENT_REQUIRED_KEYS = {"fingerprint", "event", "breadcrumbs"}
EVENT_BODY_REQUIRED_KEYS = {"type", "value", "stacktrace"}


def _init_sauron():
    mock_client = MagicMock()
    sauron._client = mock_client
    sauron._context = sauron.ExecutionContext()
    return mock_client


def _get_sent_event(mock_client) -> dict:
    mock_client.send.assert_called_once()
    return mock_client.send.call_args[0][0]


class TestExceptionEventSchema:
    def test_has_required_keys(self):
        mock_client = _init_sauron()

        try:
            raise ValueError("test error")
        except ValueError as e:
            sauron.capture_exception(e)

        event = _get_sent_event(mock_client)
        assert EVENT_REQUIRED_KEYS <= event.keys()

    def test_event_body_has_required_keys(self):
        mock_client = _init_sauron()

        try:
            raise ValueError("test error")
        except ValueError as e:
            sauron.capture_exception(e)

        event = _get_sent_event(mock_client)
        assert EVENT_BODY_REQUIRED_KEYS <= event["event"].keys()

    def test_type_is_exception_class_name(self):
        mock_client = _init_sauron()

        try:
            raise RuntimeError("boom")
        except RuntimeError as e:
            sauron.capture_exception(e)

        event = _get_sent_event(mock_client)
        assert event["event"]["type"] == "RuntimeError"

    def test_value_is_exception_message(self):
        mock_client = _init_sauron()

        try:
            raise ValueError("invalid input")
        except ValueError as e:
            sauron.capture_exception(e)

        event = _get_sent_event(mock_client)
        assert event["event"]["value"] == "invalid input"

    def test_stacktrace_has_frames(self):
        mock_client = _init_sauron()

        try:
            raise ValueError("test")
        except ValueError as e:
            sauron.capture_exception(e)

        event = _get_sent_event(mock_client)
        frames = event["event"]["stacktrace"]
        assert len(frames) > 0
        assert {"filename", "lineno", "function"} <= frames[0].keys()


class TestLogEventSchema:
    def _make_record(self, *, level="ERROR", msg="something failed", exc_info=None):
        record = logging.LogRecord(
            name="myapp.service",
            level=getattr(logging, level),
            pathname="/app/services/payment.py",
            lineno=42,
            msg=msg,
            args=None,
            exc_info=exc_info,
        )
        return record

    def test_has_required_keys(self):
        mock_client = _init_sauron()
        sauron.capture_exception_from_record(self._make_record())

        event = _get_sent_event(mock_client)
        assert EVENT_REQUIRED_KEYS <= event.keys()

    def test_event_body_has_required_keys(self):
        mock_client = _init_sauron()
        sauron.capture_exception_from_record(self._make_record())

        event = _get_sent_event(mock_client)
        assert EVENT_BODY_REQUIRED_KEYS <= event["event"].keys()

    def test_type_is_log_level(self):
        mock_client = _init_sauron()
        sauron.capture_exception_from_record(self._make_record(level="CRITICAL"))

        event = _get_sent_event(mock_client)
        assert event["event"]["type"] == "CRITICAL"

    def test_value_is_log_message(self):
        mock_client = _init_sauron()
        sauron.capture_exception_from_record(self._make_record(msg="db connection lost"))

        event = _get_sent_event(mock_client)
        assert event["event"]["value"] == "db connection lost"

    def test_stacktrace_has_frames(self):
        mock_client = _init_sauron()
        sauron.capture_exception_from_record(self._make_record())

        event = _get_sent_event(mock_client)
        frames = event["event"]["stacktrace"]
        assert len(frames) > 0
        assert {"filename", "lineno", "function"} <= frames[0].keys()


class TestLogWithExceptionEventSchema:
    def test_uses_exception_schema_when_exc_info_present(self):
        mock_client = _init_sauron()

        try:
            raise KeyError("missing_key")
        except KeyError:
            import sys
            exc_info = sys.exc_info()
            record = logging.LogRecord(
                name="myapp",
                level=logging.ERROR,
                pathname="/app/main.py",
                lineno=10,
                msg="unexpected error",
                args=None,
                exc_info=exc_info,
            )
            sauron.capture_exception_from_record(record)

        event = _get_sent_event(mock_client)
        assert EVENT_REQUIRED_KEYS <= event.keys()
        assert event["event"]["type"] == "KeyError"
        assert event["event"]["value"] == "'missing_key'"
        assert len(event["event"]["stacktrace"]) > 0
