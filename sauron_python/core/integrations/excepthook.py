import sys
from types import TracebackType
from typing import Any

from sauron_python.core.integrations import Integration


class ExcepthookIntegration(Integration):
    identifier = "excepthook"

    @staticmethod
    def setup_once() -> None:
        old_excepthook = sys.excepthook

        def sauron_excepthook(
            exc_type: type[BaseException],
            exc_value: BaseException,
            exc_tb: TracebackType | None,
        ) -> Any:
            import sauron_python.sauron_sdk as sauron

            sauron.capture_exception(exc_value)

            return old_excepthook(exc_type, exc_value, exc_tb)

        sys.excepthook = sauron_excepthook
