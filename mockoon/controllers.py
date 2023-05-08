from abc import ABC, abstractmethod

from .resources.transaction import Transaction
from .server import MockoonServer


class ServerController(ABC):
  @abstractmethod
  def start(self):
    ...

  @abstractmethod
  def stop(self):
    ...


class MockoonServerController(ServerController):
  def __init__(self, server: MockoonServer):
    self.server = server

  def start(self):
    self.server.start()

  def stop(self):
    self.server.stop()


class TransactionController(ABC):
  @property
  @abstractmethod
  def transactions(self) -> list[Transaction]:
    ...

  @abstractmethod
  def reset_transactions(self):
    ...


class MockoonTransactionController(TransactionController):
  def __init__(self, server: MockoonServer):
    self.server = server

  @property
  def transactions(self) -> list[Transaction]:
    return self.server.transactions

  def reset_transactions(self):
    self.server.reset_transactions()


class LoggingController(ABC):
  @abstractmethod
  def start_logging(self):
    ...

  @abstractmethod
  def stop_logging(self):
    ...


class HttpTransactionController(ABC):
  @abstractmethod
  def wait_for_route_hit(self, route: str):
    ...


class StateController(ABC):
  @abstractmethod
  def wait_for_active(self):
    ...


class MockoonLoggingController(LoggingController):
  def __init__(self, server: MockoonServer):
    self.server = server

  def start_logging(self):
    self.server.start_log_stream()

  def stop_logging(self):
    self.server.stop_log_stream()


class MockoonHttpTransactionController(HttpTransactionController):
  def __init__(self, server: MockoonServer):
    self.server = server

  def wait_for_route_hit(self, route: str):
    self.server.wait_for_route_hit(route)


class MockoonStateController(StateController):
  def __init__(self, server: MockoonServer):
    self.server = server

  def wait_for_active(self):
    self.server.wait_for_active()
