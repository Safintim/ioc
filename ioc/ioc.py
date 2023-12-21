from typing import Any

from ioc.container import Container, Dependencies


class Ioc:
    @classmethod
    def resolve(cls, dependency: str | Dependencies, *args: Any) -> Any:
        return Container.resolve(dependency, *args)
