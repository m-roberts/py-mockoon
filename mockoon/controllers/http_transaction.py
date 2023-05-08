
from abc import ABC, abstractmethod

from ..server import MockoonServer as Server


class HttpTransactionController(ABC):
    @abstractmethod
    def wait_for_route_hit(self, route: str):
        ...


class MockoonHttpTransactionController(HttpTransactionController):
    def __init__(self, server: Server):
        self.server = server

    def wait_for_route_hit(self, route: str):
        self.server.wait_for_route_hit(route)
