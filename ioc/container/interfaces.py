from typing import Protocol, Any


class StrategyResolver(Protocol):
    def __call__(self, *args: tuple) -> Any:
        ...


class ICommand(Protocol):
    def execute(self) -> None:
        ...
