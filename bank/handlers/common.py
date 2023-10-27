import uuid as _uuid

from depeche_db import MessageStore
from depeche_db import event_sourcing as _es

from .. import domain as _domain
from .. import messages as _messages


class AccountRepo(_es.repository.Repo[_domain.Account, _uuid.UUID]):
    pass


class TransferRepo(_es.repository.Repo[_domain.Transfer, _uuid.UUID]):
    pass


class EventStoreAccountRepo(
    AccountRepo, _es.EventStoreRepo[_messages.AppMessage, _domain.Account, _uuid.UUID]
):
    def __init__(self, event_store: MessageStore[_messages.AppMessage]):
        super().__init__(
            event_store=event_store,
            constructor=_domain.Account,
            stream_prefix="account",
        )


class EventStoreTransferRepo(
    TransferRepo, _es.EventStoreRepo[_messages.AppMessage, _domain.Transfer, _uuid.UUID]
):
    def __init__(self, event_store: MessageStore[_messages.AppMessage]):
        super().__init__(
            event_store=event_store,
            constructor=_domain.Transfer,
            stream_prefix="transfer",
        )


class AccountCommandWiter:
    def __init__(self, message_store: MessageStore[_messages.AppMessage]):
        self.message_store = message_store

    def write(self, account_id: _uuid.UUID, command: _messages.AccountCommand):
        self.message_store.write(f"account-command-{account_id}", command)
