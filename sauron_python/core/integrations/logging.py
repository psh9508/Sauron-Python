import logging
from typing import Any

from sauron_python.core.integrations import Integration


class LoggingIntegration(Integration):
    identifier = "logging"

    @staticmethod
    def setup_once() -> None:
        original_callhandlers = logging.Logger.callHandlers

        def logging_patched_callhandlers(self, record: logging.LogRecord) -> Any:
            try:
                return original_callhandlers(self, record)
            finally:
                pass
    
        logging.Logger.callHandlers = logging_patched_callhandlers