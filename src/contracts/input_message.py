from abc import ABC, abstractmethod


class InputMessage(ABC):
    @abstractmethod
    def get_content(self) -> str:
        pass  # pragma: no cover
