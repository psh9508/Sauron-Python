import logging
from typing import Any

from sauron_python.core.integrations import Integration

DEFAULT_BREADCRUMB_LEVEL = logging.INFO
DEFAULT_EVENT_LEVEL = logging.ERROR

_IGNORED_LOGGERS: set[str] = {"sauron_python", "httpx", "httpcore"}


def ignore_logger(name: str) -> None:
    _IGNORED_LOGGERS.add(name)


class LoggingIntegration(Integration):
    identifier = "logging"

    @staticmethod
    def setup_once() -> None:
        original_callhandlers = logging.Logger.callHandlers

        def logging_patched_callhandlers(self, record: logging.LogRecord) -> Any:
            try:
                return original_callhandlers(self, record)
            finally:
                ignored = _IGNORED_LOGGERS
                name = record.name.strip()

                if any(name == ig or name.startswith(ig + ".") for ig in ignored):
                    return

                import sauron_python.sauron_sdk as sauron

                ctx = sauron.get_context()
                if ctx is None:
                    return

                if record.levelno >= DEFAULT_BREADCRUMB_LEVEL:
                    ctx.add_breadcrumb({
                        "type": "log",
                        "level": record.levelname.lower(),
                        "category": record.name,
                        "message": record.getMessage(),
                    })

                if record.levelno >= DEFAULT_EVENT_LEVEL:
                    sauron.capture_exception_from_record(record)

        logging.Logger.callHandlers = logging_patched_callhandlers
