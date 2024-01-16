import time
import pytest
from threading import Thread
from ioc import Ioc
from ioc.container import (
    Container,
    IocDependencyNotFoundError,
    ScopeRootNotHaveParentScope,
)


def test_parent_scope_for_root() -> None:
    with pytest.raises(ScopeRootNotHaveParentScope):
        Ioc.resolve("ioc.scope.parent")


def test_resolve_not_exists_dependency() -> None:
    with pytest.raises(IocDependencyNotFoundError):
        Ioc.resolve("service1")


def test_register_constants() -> None:
    api_timeout: int = 20

    with Ioc.resolve("ioc.scope.new"):
        Ioc.resolve("ioc.register", "api_timeout", lambda *args: api_timeout).execute()
        actual_timeout: int = Ioc.resolve("api_timeout")
        assert actual_timeout == api_timeout


def test_register() -> None:
    class Service:
        def __init__(self, param: str) -> None:
            self.param = param

        def get_param(self) -> str:
            return self.param

    param: str = "hello"
    with Ioc.resolve("ioc.scope.new"):
        Ioc.resolve(
            "ioc.register", "service1", lambda *args: Service(args[0])
        ).execute()
        service1: Service = Ioc.resolve("service1", param)
        service2: Service = Ioc.resolve("service1", param)

    assert isinstance(service1, Service)
    assert service1 != service2
    assert service1.get_param() == param


def test_ioc_local_scope_threads() -> None:
    api_timeout: int = 10

    def register_api_timeout(api_timeout: int) -> None:
        scope = Container.resolve("ioc.scope.create")
        Ioc.resolve("ioc.scope.current.set", scope).execute()

        Ioc.resolve("ioc.register", "api_timeout", lambda *args: api_timeout)

    def try_resolve_api_timeout() -> None:
        time.sleep(0.3)

        with pytest.raises(IocDependencyNotFoundError):
            Ioc.resolve("api_timeout")

    threads: list[Thread] = [
        Thread(target=register_api_timeout, args=(api_timeout,)),
        Thread(target=try_resolve_api_timeout),
    ]

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()


def test_ioc_local_scope_threads2() -> None:
    api_timeout: int = 10

    def register_api_timeout_and_try_resolve_service(api_timeout: int) -> None:
        time.sleep(0.3)
        scope = Container.resolve("ioc.scope.create")
        Ioc.resolve("ioc.scope.current.set", scope).execute()

        Ioc.resolve("ioc.register", "api_timeout", lambda *args: api_timeout)

        with pytest.raises(IocDependencyNotFoundError):
            Ioc.resolve("service")

    def register_service_and_try_resolve_api_timeout() -> None:
        scope = Container.resolve("ioc.scope.create")
        Ioc.resolve("ioc.scope.current.set", scope).execute()
        Ioc.resolve("ioc.register", "service", lambda *args: "service")

        with pytest.raises(IocDependencyNotFoundError):
            Ioc.resolve("api_timeout")

    threads: list[Thread] = [
        Thread(
            target=register_api_timeout_and_try_resolve_service, args=(api_timeout,)
        ),
        Thread(target=register_service_and_try_resolve_api_timeout),
    ]

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()
