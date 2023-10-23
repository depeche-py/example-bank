from . import config as _config
import sqlalchemy as _sa
from depeche_db import (
    MessageStore,
    AggregatedStream,
    Subscription,
    MessagePartitioner,
    StoredMessage,
)
from depeche_db.tools import PydanticMessageSerializer

from . import di as _di
from .handlers import commands, repositories, queries
from . import messages as _messages

# TODO fix import
from depeche_db._subscription import CallMiddleware


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
    container.register(repositories.AccountRepo, repositories.EventStoreAccountRepo)
    container.register(repositories.TransferRepo, repositories.EventStoreTransferRepo)
    container.register(
        commands.CommandHandler, lambda: commands.CommandHandler(container)
    )
    container.register(queries.QueryHandler, queries.QueryHandler)
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
        print("DiMiddleware", handler, repr(message))
        container = get_di_container()
        injector = _di.Injector(container)
        return injector.inject(handler, **{self.message_key: message})


def get_runnables():
    from .handlers import commands, events

    message_store = _message_store()

    account_commands = AggregatedStream(
        name="account_commands",
        store=message_store,
        partitioner=PartitionByAccountId(),
        stream_wildcards=["account-command-%"],
    )

    account_commands_subscription = Subscription(
        name="account_commands_subscription",
        stream=account_commands,
        call_middleware=DiMiddleware("command"),
    )
    account_commands_subscription.handler.register(
        commands.handle_async_account_commands
    )

    account_events = AggregatedStream(
        name="account_events",
        store=message_store,
        partitioner=PartitionByAccountId(),
        stream_wildcards=["account-%"],
    )

    transfer_account_subscription = Subscription(
        # TODO rename
        name="transfer_subscribtion",
        stream=account_events,
        call_middleware=DiMiddleware("event"),
    )
    transfer_account_subscription.handler.register(events.handle_account_withdrawn)
    transfer_account_subscription.handler.register(events.handle_account_deposited)

    transfer_events = AggregatedStream(
        name="transfer_events",
        store=message_store,
        partitioner=PartitionByTransferId(),
        stream_wildcards=["transfer-%"],
    )

    transfer_subscribtion = Subscription(
        # TODO rename
        name="transfer_subscribtion1",
        stream=transfer_events,
        call_middleware=DiMiddleware("event"),
    )
    transfer_subscribtion.handler.register(events.handle_transfer_initiated)
    transfer_subscribtion.handler.register(events.handle_transfer_withdrawn)

    return [
        account_commands.projector,
        account_events.projector,
        transfer_events.projector,
        account_commands_subscription.handler,
        transfer_account_subscription.handler,
        transfer_subscribtion.handler,
    ]
