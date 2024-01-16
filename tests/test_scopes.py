import pytest
from ioc import Ioc
from ioc.container import Container, IocDependencyNotFoundError


def test_create_empty_scope() -> None:
    assert Ioc.resolve("ioc.scope.create.empty") == {}


def test_create_new_scope() -> None:
    scope = Ioc.resolve("ioc.scope.create")
    Ioc.resolve("ioc.scope.create")
    assert scope["ioc.scope.parent"]() == Container.root_scope


def test_create_new_scope_with_parent() -> None:
    current_scope = Ioc.resolve("ioc.scope.current")
    scope = Ioc.resolve("ioc.scope.create", current_scope)
    assert scope["ioc.scope.parent"]() == current_scope


def test_current_scope() -> None:
    assert Ioc.resolve("ioc.scope.current")


def test_clear_current_scope_if_empty() -> None:
    assert Ioc.resolve("ioc.scope.current") == Container.root_scope

    Ioc.resolve("ioc.scope.current.clear").execute()

    assert Ioc.resolve("ioc.scope.current") == Container.root_scope


def test_clear_current_scope() -> None:
    assert Ioc.resolve("ioc.scope.current") == Container.root_scope

    new_scope = Ioc.resolve("ioc.scope.create")
    Ioc.resolve("ioc.scope.current.set", new_scope).execute()

    assert Ioc.resolve("ioc.scope.current") == new_scope

    Ioc.resolve("ioc.scope.current.clear").execute()

    assert Ioc.resolve("ioc.scope.current") == Container.root_scope


def test_set_current_scope() -> None:
    new_scope = Container.resolve("ioc.scope.create")
    Ioc.resolve("ioc.scope.current.set", new_scope).execute()

    assert Ioc.resolve("ioc.scope.current") == new_scope

    Ioc.resolve("ioc.scope.current.clear").execute()


def test_new_scope() -> None:
    assert Ioc.resolve("ioc.scope.current") == Container.root_scope

    with Ioc.resolve("ioc.scope.new") as new_scope:
        assert new_scope == Container.root_scope
        assert Ioc.resolve("ioc.scope.current") == new_scope

        api_timeout: int = 10
        Ioc.resolve("ioc.register", "api_timeout", lambda *args: api_timeout).execute()
        assert Ioc.resolve("api_timeout") == api_timeout

        scope = Container.resolve("ioc.scope.create")
        Ioc.resolve("ioc.scope.current.set", scope).execute()

        assert Ioc.resolve("ioc.scope.current") == scope

    with pytest.raises(IocDependencyNotFoundError):
        Ioc.resolve("api_timeout")

    assert Ioc.resolve("ioc.scope.current") == Container.root_scope
