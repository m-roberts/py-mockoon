from abc import ABC, abstractmethod

from ..server import MockoonServer as Server


class ServerController(ABC):
    @abstractmethod
    def start(self):
        ...

    @abstractmethod
    def stop(self):
        ...


class MockoonServerController(ServerController):
    def __init__(self, server: Server):
        self.server = server

    def start(self):
        self.server.start()

    def stop(self):
        self.server.stop()