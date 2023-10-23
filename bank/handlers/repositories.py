import uuid as _uuid
from .. import event_sourcing as _es
from .. import messages as _messages
from .. import domain as _domain
from depeche_db import MessageStore


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