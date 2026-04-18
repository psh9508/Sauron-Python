
from abc import ABC, abstractmethod


class Integration(ABC):
    identifier: "str" = None  # type: ignore[assignment]

    @staticmethod
    @abstractmethod
    def setup_once() -> None:
        pass
