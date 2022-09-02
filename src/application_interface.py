from abc import ABCMeta, abstractmethod
from typing import List


class Application(metaclass=ABCMeta):
    @classmethod
    def __subclasshook__(cls, subclass):
        return hasattr(subclass, "exec") and callable(subclass.exec)

    @abstractmethod
    def exec(self, args: List[str], out: List[str], in_pipe: bool) -> None:
        """executes the application"""
        raise NotImplementedError
