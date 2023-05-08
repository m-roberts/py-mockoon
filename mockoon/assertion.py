from abc import ABC, abstractmethod

from .models import Request
from .server import MockoonServer


class TransactionAssertion(ABC):
    @property
    @abstractmethod
    def call_count(self):
        ...

    @property
    @abstractmethod
    def called(self):
        ...

    @property
    @abstractmethod
    def call_request(self):
        ...

    @property
    @abstractmethod
    def call_requests_list(self):
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
    def assert_called_once_with(self, request):
        ...

    @abstractmethod
    def assert_called_with(self, request):
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


class MockoonTransactionAssertion(TransactionAssertion):
    def __init__(self, server: MockoonServer):
        self.server = server

    @property
    def call_count(self):
        """Return the number of calls to the mock server."""
        return len(self.server.transactions)

    @property
    def called(self):
        """Return True if the mock server was called at least once, False otherwise."""
        return bool(self.server.transactions)

    @property
    def call_request(self):
        """Return the last request to the mock server."""
        return (
            self.server.transactions[-1].request if self.server.transactions else None
        )

    @property
    def call_requests_list(self):
        """Return the list of requests to the mock server."""
        return [t.request for t in self.server.transactions]

    def assert_not_called(self):
        """Assert the mock server was never called."""
        assert not self.called

    def assert_called(self):
        """Assert the mock server was called at least once."""
        assert self.called

    def assert_called_once(self):
        """Assert the mock server was called exactly once."""
        assert self.call_count == 1

    def _get_no_of_calls_with_request(self, request):
        """Return the number of calls that the server has that matches a request."""
        return self.call_requests_list.count(request)

    def assert_called_once_with(self, request):
        """Assert the mock server was called exactly once with the specified arguments."""
        assert self._get_no_of_calls_with_request(request) == 1

    def assert_called_with(self, request):
        """Assert the mock server was last called with the specified arguments."""
        assert self._get_no_of_calls_with_request(request) > 0

    def assert_has_calls(self, requests: list[Request], *, any_order=False):
        """Assert the mock server has been called with the specified calls."""
        if any_order:
            remaining_requests = self.call_requests_list.copy()
            for request in requests:
                if request in remaining_requests:
                    remaining_requests.remove(request)
                else:
                    msg = f"Expected call not found: {request}"
                    raise AssertionError(msg)
        else:
            matched_request_count = 0
            for actual_request in self.call_requests_list:
                if requests[matched_request_count] == actual_request:
                    matched_request_count += 1
                    if matched_request_count == len(requests):
                        break

            if matched_request_count != len(requests):
                msg = f"Expected calls {requests} not found in the same order in {self.call_requests_list}"
                raise AssertionError(
                    msg,
                )

    def _request_matches(self, actual_request, **kwargs):
        """Check if the actual request matches the specified properties."""
        for key, value in kwargs.items():
            if (
                not hasattr(actual_request, key)
                or getattr(actual_request, key) != value
            ):
                return False
        return True

    def _get_no_of_calls_with_properties(self, **kwargs):
        """Return the number of calls that the server has that matches the specified properties."""
        return sum(
            1
            for request in self.call_requests_list
            if self._request_matches(request, **kwargs)
        )

    def assert_called_once_with_properties(self, **kwargs):
        """Assert the mock server was called exactly once with the specified properties."""
        assert self._get_no_of_calls_with_properties(**kwargs) == 1

    def assert_called_with_properties(self, **kwargs):
        """Assert the mock server was last called with the specified properties."""
        assert self._get_no_of_calls_with_properties(**kwargs) > 0

    def assert_has_calls_with_properties(self, calls, *, any_order=False):
        """Assert the mock server has been called with the specified calls, each containing the specified properties."""
        if any_order:
            remaining_requests = self.call_requests_list.copy()
            for call in calls:
                matching_request = next(
                    (
                        request
                        for request in remaining_requests
                        if self._request_matches(request, **call)
                    ),
                    None,
                )
                if matching_request:
                    remaining_requests.remove(matching_request)
                else:
                    msg = f"Expected call not found: {call}"
                    raise AssertionError(msg)
        else:
            matched_call_count = 0
            for actual_request in self.call_requests_list:
                if self._request_matches(actual_request, **calls[matched_call_count]):
                    matched_call_count += 1
                    if matched_call_count == len(calls):
                        break

            if matched_call_count != len(calls):
                msg = f"Expected calls {calls} not found in the same order in {self.call_requests_list}"
                raise AssertionError(
                    msg,
                )
