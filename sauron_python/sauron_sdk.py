import logging
import sys
import traceback
from contextvars import ContextVar
from typing import Sequence

from sauron_python.core.integrations import Integration
from sauron_python.core.integrations.excepthook import ExcepthookIntegration
from sauron_python.core.integrations.logging import LoggingIntegration
from sauron_python.core.suron_client import SauronClient
from sauron_python.models.execution_context import ExecutionContext

_DEFAULT_INTEGRATIONS: list[type[Integration]] = [
    LoggingIntegration,
    ExcepthookIntegration,
]

_client: ContextVar[SauronClient | None] = ContextVar("sauron_client", default=None)
_context: ContextVar[ExecutionContext | None] = ContextVar("execution_context", default=None)


def _setup_integrations(integrations: Sequence[type[Integration]]) -> None:
    for integration in integrations:
        integration.setup_once()


def init(*, repository_id: int, endpoint: str):
    _client.set(SauronClient(repository_id=repository_id, endpoint=endpoint))
    _context.set(ExecutionContext())
    _setup_integrations(_DEFAULT_INTEGRATIONS)


def get_client() -> SauronClient | None:
    return _client.get()


def get_context() -> ExecutionContext | None:
    return _context.get()


def add_breadcrumb(crumb: dict):
    ctx = get_context()
    if ctx is not None:
        ctx.add_breadcrumb(crumb)


def capture_message(message: str):
    client = get_client()
    if client is None:
        return
    client.send({"message": message})


def capture_exception(error: BaseException | None = None):
    client = get_client()
    if client is None:
        return

    if error is None:
        exc_info = sys.exc_info()
        if exc_info[0] is None:
            return
        error = exc_info[1]

    ctx = get_context()
    breadcrumbs = list(ctx._breadcrumbs) if ctx is not None else []

    tb = error.__traceback__
    frames = []
    if tb is not None:
        for filename, lineno, name, line in traceback.extract_tb(tb):
            frame = {
                "filename": filename,
                "lineno": lineno,
                "function": name,
            }
            if line:
                frame["code"] = line
            frames.append(frame)

    event = {
        "exception": {
            "type": type(error).__name__,
            "value": str(error),
            "stacktrace": frames,
        },
        "breadcrumbs": breadcrumbs,
    }

    client.send(event)


def capture_exception_from_record(record: logging.LogRecord):
    client = get_client()
    if client is None:
        return

    ctx = get_context()
    breadcrumbs = list(ctx._breadcrumbs) if ctx is not None else []

    event: dict = {
        "exception": {
            "type": record.levelname,
            "value": record.getMessage(),
            "category": record.name,
        },
        "breadcrumbs": breadcrumbs,
    }

    if record.exc_info and record.exc_info[1] is not None:
        error = record.exc_info[1]
        tb = error.__traceback__
        frames = []
        if tb is not None:
            for filename, lineno, name, line in traceback.extract_tb(tb):
                frame = {
                    "filename": filename,
                    "lineno": lineno,
                    "function": name,
                }
                if line:
                    frame["code"] = line
                frames.append(frame)

        event["exception"]["type"] = type(error).__name__
        event["exception"]["value"] = str(error)
        event["exception"]["stacktrace"] = frames

    client.send(event)
