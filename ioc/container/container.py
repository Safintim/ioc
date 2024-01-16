from typing import Any, Generator, Literal
from threading import local
from contextlib import contextmanager

from ioc.container.exceptions import (
    IocDependencyNotFoundError,
    ScopeRootNotHaveParentScope,
)
from ioc.container.interfaces import StrategyResolver, ICommand

Dependencies = (
    str
    | Literal[
        "ioc.register",
        "ioc.scope.current",
        "ioc.scope.parent",
        "ioc.scope.create",
        "ioc.scope.current.set",
        "ioc.scope.create.empty",
        "ioc.scope.current.clear",
        "ioc.scope.new",
    ]
)
Scope = dict[Dependencies, StrategyResolver]


class RegisterCommand:
    def __init__(self, dependency: str, dependecy_strategy: StrategyResolver) -> None:
        self.dependency = dependency
        self.dependecy_strategy: StrategyResolver = dependecy_strategy

    def execute(self) -> None:
        scope: Scope = Container.resolve("ioc.scope.current")
        scope[self.dependency] = self.dependecy_strategy


class SetCurrentScope:
    def __init__(self, scope: Scope) -> None:
        self.new_scope: Scope = scope

    def execute(self) -> None:
        Container.local_scope.value = self.new_scope


class ClearCurrentScope:
    def execute(self) -> None:
        Container.local_scope.value = None


def register_command_resolver(*args: Any) -> ICommand:
    return RegisterCommand(args[0], args[1])


def scope_current_resolver(*args: Any) -> Scope:
    return (
        Container.root_scope
        if getattr(Container.local_scope, "value", None) is None
        else Container.local_scope.value
    )


def scope_parent_resolver(*args: Any) -> None:
    raise ScopeRootNotHaveParentScope("Root scope does not have a parent scope")


def scope_set_current_resolver(*args: Any) -> ICommand:
    return SetCurrentScope(args[0])


def create_scope_resolver(*args: Any) -> Scope:
    parent_scope: Scope
    if len(args) > 0:
        parent_scope = args[0]
    else:
        parent_scope = Container.resolve("ioc.scope.current")

    scope: Scope = Container.resolve("ioc.scope.create.empty")
    scope["ioc.scope.parent"] = lambda *args: parent_scope
    return scope


def scope_create_empty_resolver(*args: Any) -> Scope:
    return {}


def scope_clear_current_resolver(*args: Any) -> ICommand:
    return ClearCurrentScope()


@contextmanager
def scope_new_resolver(*args: Any) -> Generator[Scope, Any, None]:
    scope: Scope = Container.resolve("ioc.scope.create.empty")
    scope = {**Container.root_scope}
    original_local_scope: Scope = Container.resolve("ioc.scope.current")

    Container.resolve("ioc.scope.current.set", scope).execute()
    try:
        yield scope
    finally:
        Container.resolve("ioc.scope.current.set", original_local_scope).execute()


class Container:
    local_scope: local = local()
    root_scope: Scope = {
        "ioc.register": register_command_resolver,
        "ioc.scope.current": scope_current_resolver,
        "ioc.scope.parent": scope_parent_resolver,
        "ioc.scope.create": create_scope_resolver,
        "ioc.scope.current.set": scope_set_current_resolver,
        "ioc.scope.create.empty": scope_create_empty_resolver,
        "ioc.scope.current.clear": scope_clear_current_resolver,
        "ioc.scope.new": scope_new_resolver,
    }

    @classmethod
    def resolve(cls, dependency: str | Dependencies, *args: Any) -> Any:
        scope: Scope = (
            cls.root_scope
            if getattr(cls.local_scope, "value", None) is None
            else cls.local_scope.value
        )

        while True:
            dependency_resolver: StrategyResolver | None = scope.get(dependency)
            if dependency_resolver:
                return dependency_resolver(*args)
            try:
                scope = scope["ioc.scope.parent"]()
            except ScopeRootNotHaveParentScope as exc:
                raise IocDependencyNotFoundError("Not found dependecy") from exc
