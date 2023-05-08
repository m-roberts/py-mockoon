from datetime import datetime

from polyfactory import Use
from polyfactory.factories.pydantic_factory import ModelFactory
from polyfactory.pytest_plugin import register_fixture

from mockoon.models import LogMessage, Transaction

possible_messages = ["Message 1", "Message 2", "Message 3"]

class LogMessageFactory(ModelFactory[LogMessage]):
    __model__ = LogMessage

    level = "info"
    message = Use(ModelFactory.__random__.choice, possible_messages)
    timestamp = lambda: datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'


log_message_factory_fixture = register_fixture(LogMessageFactory)


def test_log_message_factory(log_message_factory: LogMessageFactory) -> None:
    # This only really tests that the factory above produces correct data
    # - note that the factory is not used outside of the test suite...
    log_message_instance = log_message_factory.build()

    assert isinstance(log_message_instance, LogMessage)
    assert isinstance(log_message_instance.level, str)
    assert log_message_instance.level == "info"
    assert isinstance(log_message_instance.message, str)
    assert log_message_instance.message in possible_messages
    assert isinstance(log_message_instance.timestamp, str)
    assert isinstance(log_message_instance.mockName, str | None)
    assert isinstance(log_message_instance.transaction, Transaction | None)
