import logging

logger = logging.getLogger("sauron_python.core.safe")


class _CaptureInternalException:
    __slots__ = ()

    def __enter__(self):
        return self

    def __exit__(self, ty, value, tb):
        if ty is not None and value is not None:
            logger.debug("Internal error in sauron_sdk", exc_info=(ty, value, tb))
        return True


_INSTANCE = _CaptureInternalException()


def capture_internal_exceptions():
    return _INSTANCE
