from abc import ABC, abstractmethod

from .assertion import MockoonTransactionAssertion
from .controllers import (
    MockoonHttpTransactionController,
    MockoonLoggingController,
    MockoonServerController,
    MockoonStateController,
    MockoonTransactionController,
)
from .resources.request import Request
from .resources.transaction import Transaction
from .server import MockoonServer


class API(ABC):
    @abstractmethod
    def start_logging(self):
        ...

    @abstractmethod
    def stop_logging(self):
        ...

    @abstractmethod
    def wait_for_route_hit(self, route: str):
        ...

    @abstractmethod
    def wait_for_active(self):
        ...

    @abstractmethod
    def __enter__(self):
        ...

    @abstractmethod
    def __exit__(self, exc_type, exc_value, traceback):
        ...

    @abstractmethod
    def start(self):
        ...

    @abstractmethod
    def stop(self):
        ...

    @abstractmethod
    def transactions(self) -> list[Transaction]:
        ...

    @abstractmethod
    def reset_transactions(self):
        ...

    @abstractmethod
    def assert_not_called(self):
        ...

    @abstractmethod
    def assert_called(self):
        ...

    @abstractmethod
    def assert_called_once(self):
        ...

    @abstractmethod
    def assert_called_once_with(self, request: Request):
        ...

    @abstractmethod
    def assert_called_with(self, request: Request):
        ...

    @abstractmethod
    def assert_has_calls(self, requests: list[Request], *, any_order=False):
        ...

    @abstractmethod
    def assert_called_once_with_properties(self, **kwargs):
        ...

    @abstractmethod
    def assert_called_with_properties(self, **kwargs):
        ...

    @abstractmethod
    def assert_has_calls_with_properties(self, calls, *, any_order=False):
        ...


class MockoonAPI:
    def __init__(
        self,
        data_file: str,
        hostname: str | None = None,
        port: int | None = None,
        pname: str | None = None,
        *,
        use_docker: bool = False,
        repair: bool | None = False,
    ):
        self.server = MockoonServer(
            data_file,
            hostname,
            port,
            pname,
            use_docker=use_docker,
            repair=repair,
        )
        self.server_controller = MockoonServerController(self.server)
        self.transaction_controller = MockoonTransactionController(self.server)
        self.logging_controller = MockoonLoggingController(self.server)
        self.http_transaction_controller = MockoonHttpTransactionController(self.server)
        self.state_controller = MockoonStateController(self.server)
        self.assertions = MockoonTransactionAssertion(self.server)

    def start_logging(self):
        self.logging_controller.start_logging()

    def stop_logging(self):
        self.logging_controller.stop_logging()

    def wait_for_route_hit(self, route: str):
        self.http_transaction_controller.wait_for_route_hit(route)

    def wait_for_active(self):
        self.state_controller.wait_for_active()

    def __enter__(self):
        """Start the MockoonServer and return the instance when used in a 'with' statement."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Stop the MockoonServer when exiting a 'with' statement."""
        self.stop()

    def start(self):
        self.server_controller.start()

    def stop(self):
        self.server_controller.stop()

    @property
    def root_uri(self):
        return self.server.root_uri

    @property
    def transactions(self) -> list[Transaction]:
        return self.transaction_controller.transactions

    def reset_transactions(self):
        self.transaction_controller.reset_transactions()

    def assert_not_called(self):
        self.assertions.assert_not_called()

    def assert_called(self):
        self.assertions.assert_called()

    def assert_called_once(self):
        self.assertions.assert_called_once()

    def assert_called_once_with(self, request: Request):
        self.assertions.assert_called_once_with(request)

    def assert_called_with(self, request: Request):
        self.assertions.assert_called_with(request)

    def assert_has_calls(self, requests: list[Request], *, any_order=False):
        self.assertions.assert_has_calls(requests, any_order=any_order)

    def assert_called_once_with_properties(self, **kwargs):
        self.assertions.assert_called_once_with_properties(**kwargs)

    def assert_called_with_properties(self, **kwargs):
        self.assertions.assert_called_with_properties(**kwargs)

    def assert_has_calls_with_properties(self, calls, *, any_order=False):
        self.assertions.assert_has_calls_with_properties(calls, any_order=any_order)
