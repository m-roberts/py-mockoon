from dataclasses import dataclass

from .transaction import Transaction


@dataclass
class LogMessage:
    level: str
    message: str
    timestamp: str
    mockName: str | None  # noqa: N815
    transaction: Transaction | None

    @classmethod
    def from_log_entry(cls, log_entry):
        _transaction = None

        if "transaction" in log_entry:
            _transaction = Transaction.from_log_entry(log_entry["transaction"])
            del log_entry["transaction"]

        # Not all messages relate to a mock - e.g. proxy creation
        if "mockName" not in log_entry:
            log_entry["mockName"] = None

        return cls(transaction=_transaction, **log_entry)
