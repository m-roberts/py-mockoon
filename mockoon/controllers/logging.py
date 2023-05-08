from abc import ABC, abstractmethod

from ..server import MockoonServer as Server


class LoggingController(ABC):
    @abstractmethod
    def start_logging(self):
        ...

    @abstractmethod
    def stop_logging(self):
        ...


class MockoonLoggingController(LoggingController):
    def __init__(self, server: Server):
        self.server = server

    def start_logging(self):
        self.server.start_log_stream()

    def stop_logging(self):
        self.server.stop_log_stream()
