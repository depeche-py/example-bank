import explicit_di as _di
import sqlalchemy as _sa
from depeche_db import (
    CallMiddleware,
    Executor,
    MessagePartitioner,
    MessageStore,
    StoredMessage,
)
from depeche_db.tools import PydanticMessageSerializer

from . import config as _config
from . import messages as _messages
from .handlers import commands, common, queries


def _message_store() -> MessageStore:
    config = _config.get()
    return MessageStore(
        name="aaa",
        engine=_sa.create_engine(config.db_dsn.get_secret_value()),
        serializer=PydanticMessageSerializer(_messages.AppMessage),
    )


def get_di_container() -> _di.Container:
    container = _di.Container()
    container.register(_di.Container, lambda: container)
    container.register(MessageStore[_messages.AppMessage], _message_store)
    container.register(common.AccountRepo, common.EventStoreAccountRepo)
    container.register(common.TransferRepo, common.EventStoreTransferRepo)
    container.register(common.AccountCommandWiter)
    container.register(commands.CommandHandlerWithDI)
    container.register(queries.QueryHandler)
    return container


class PartitionByAccountId(MessagePartitioner[_messages.AppMessage]):
    def get_partition(self, message: StoredMessage[_messages.AppMessage]) -> int:
        msg = message.message
        if isinstance(msg, _messages.AccountCommand):  # type: ignore
            if not msg.account_id:  # type: ignore
                return 0
            return msg.account_id.int % 10  # type: ignore
        if isinstance(msg, _messages.AccountEvent):  # type: ignore
            return msg.account_id.int % 10  # type: ignore
        raise NotImplementedError()


class PartitionByTransferId(MessagePartitioner[_messages.AppMessage]):
    def get_partition(self, message: StoredMessage[_messages.AppMessage]) -> int:
        msg = message.message
        if isinstance(msg, _messages.TransferEvent):  # type: ignore
            return msg.transfer_id.int % 10  # type: ignore
        raise NotImplementedError()


class DiMiddleware(CallMiddleware):
    def __init__(self, message_key: str = "message"):
        self.message_key = message_key

    def call(self, handler, message):
        container = get_di_container()
        return container.inject(handler, **{self.message_key: message})


def get_runnables():
    from .handlers import commands, events

    message_store = _message_store()

    account_commands = message_store.aggregated_stream(
        name="account_commands",
        partitioner=PartitionByAccountId(),
        stream_wildcards=["account-command-%"],
    )

    account_commands_subscription = account_commands.subscription(
        name="account_commands_subscription",
        handlers=commands.CommandHandler(),
        call_middleware=DiMiddleware("command"),
    )

    account_events = message_store.aggregated_stream(
        name="account_events",
        partitioner=PartitionByAccountId(),
        stream_wildcards=["account-%"],
    )

    account_subscription = account_events.subscription(
        name="account_subscription",
        handlers=events.AccountHandler(),
        call_middleware=DiMiddleware("event"),
    )

    transfer_events = message_store.aggregated_stream(
        name="transfer_events",
        partitioner=PartitionByTransferId(),
        stream_wildcards=["transfer-%"],
    )
    transfer_subscription = transfer_events.subscription(
        name="transfer_subscription",
        handlers=events.TransferHandler(),
        call_middleware=DiMiddleware("event"),
    )

    return [
        account_commands.projector,
        account_events.projector,
        transfer_events.projector,
        account_commands_subscription.runner,
        account_subscription.runner,
        transfer_subscription.runner,
    ]


def main():
    config = _config.get()
    executor = Executor(db_dsn=config.db_dsn.get_secret_value())
    for runnable in get_runnables():
        executor.register(runnable)
    executor.run()


if __name__ == "__main__":
    main()
