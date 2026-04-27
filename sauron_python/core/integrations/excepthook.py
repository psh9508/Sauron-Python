import sys
from types import TracebackType
from typing import Any

from sauron_python.core.integrations import Integration
from sauron_python.core.safe import capture_internal_exceptions


class ExcepthookIntegration(Integration):
    identifier = "excepthook"

    @staticmethod
    def _install() -> None:
        old_excepthook = sys.excepthook

        def sauron_excepthook(
            exc_type: type[BaseException],
            exc_value: BaseException,
            exc_tb: TracebackType | None,
        ) -> Any:
            import sauron_python.sauron_sdk as sauron

            with capture_internal_exceptions():
                sauron.capture_exception(exc_value)

            return old_excepthook(exc_type, exc_value, exc_tb)

        sys.excepthook = sauron_excepthook
