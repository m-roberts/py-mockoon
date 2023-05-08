from abc import ABC, abstractmethod

from ..models.transaction import Transaction
from ..server import MockoonServer as Server


class TransactionController(ABC):
    @property
    @abstractmethod
    def transactions(self) -> list[Transaction]:
        ...

    @abstractmethod
    def reset_transactions(self):
        ...


class MockoonTransactionController(TransactionController):
    def __init__(self, server: Server):
        self.server = server

    @property
    def transactions(self) -> list[Transaction]:
        return self.server.transactions

    def reset_transactions(self):
        self.server.reset_transactions()
