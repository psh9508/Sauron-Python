
from abc import ABC, abstractmethod


class Integration(ABC):
    identifier: "str" = None  # type: ignore[assignment]
    _installed: bool = False

    @classmethod
    def setup_once(cls) -> None:
        if cls._installed:
            return
        cls._install()
        cls._installed = True

    @staticmethod
    @abstractmethod
    def _install() -> None:
        pass
