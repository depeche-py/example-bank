from . import config as _config
import sqlalchemy as _sa
from depeche_db import (
    MessageStore,
    AggregatedStream,
    Subscription,
    MessagePartitioner,
    StoredMessage,
    SubscriptionRunner,
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
    )
    account_commands_subscription_runner = SubscriptionRunner.create(
        subscription=account_commands_subscription,
        handlers=commands.CommandHandler(),
        call_middleware=DiMiddleware("command"),
    )

    account_events = AggregatedStream(
        name="account_events",
        store=message_store,
        partitioner=PartitionByAccountId(),
        stream_wildcards=["account-%"],
    )

    account_subscription = Subscription(
        # TODO rename
        name="account_subscription",
        stream=account_events,
    )
    account_subscription_runner = SubscriptionRunner.create(
        subscription=account_subscription,
        handlers=events.AccountHandler(),
        call_middleware=DiMiddleware("event"),
    )

    transfer_events = AggregatedStream(
        name="transfer_events",
        store=message_store,
        partitioner=PartitionByTransferId(),
        stream_wildcards=["transfer-%"],
    )
    transfer_subscription = Subscription(
        name="transfer_subscription",
        stream=transfer_events,
    )
    transfer_subscription_runner = SubscriptionRunner.create(
        subscription=transfer_subscription,
        handlers=events.TransferHandler(),
        call_middleware=DiMiddleware("event"),
    )

    return [
        account_commands.projector,
        account_events.projector,
        transfer_events.projector,
        account_commands_subscription_runner,
        account_subscription_runner,
        transfer_subscription_runner,
    ]
