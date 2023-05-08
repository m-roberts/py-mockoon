from abc import ABC, abstractmethod

from ..server import MockoonServer


class StateController(ABC):
    @abstractmethod
    def wait_for_active(self):
        ...

class MockoonStateController(StateController):
    def __init__(self, server: MockoonServer):
        self.server = server

    def wait_for_active(self):
        self.server.wait_for_active()
