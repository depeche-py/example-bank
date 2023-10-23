import uuid as _uuid
from .. import event_sourcing as _es
from .. import messages as _messages


class Account(_es.EventSourcedAggregateRoot[_uuid.UUID, _messages.AccountEvent]):
    id: _uuid.UUID
    number: str

    def get_id(self) -> _uuid.UUID | None:
        if hasattr(self, "id"):
            return self.id
        return None

    def _apply(self, event: _messages.AccountEvent) -> None:
        if isinstance(event, _messages.AccountCreatedEvent):
            self.id = event.account_id
            self.number = event.account_number
            self.balance = 0
        elif isinstance(event, _messages.DepositedEvent):
            self.balance += event.amount
        elif isinstance(event, _messages.WithdrawnEvent):
            self.balance -= event.amount
        else:
            raise NotImplementedError(f"Event {type(event)} is not supported")

    @property
    def version(self) -> int:
        return self._version

    @classmethod
    def create(cls, account_id: _uuid.UUID, number: str) -> "Account":
        account = cls()
        account.apply(
            _messages.AccountCreatedEvent(account_id=account_id, account_number=number)
        )
        return account

    def deposit(self, amount: int, transfer_id: _uuid.UUID | None = None) -> None:
        self.apply(
            _messages.DepositedEvent(
                account_id=self.id, amount=amount, transfer_id=transfer_id
            )
        )

    def withdraw(self, amount: int, transfer_id: _uuid.UUID | None = None) -> None:
        self.apply(
            _messages.WithdrawnEvent(
                account_id=self.id, amount=amount, transfer_id=transfer_id
            )
        )


class Transfer(_es.EventSourcedAggregateRoot[_uuid.UUID, _messages.TransferEvent]):
    id: _uuid.UUID
    from_account_id: _uuid.UUID
    to_account_id: _uuid.UUID
    amount: int
    status: str

    def get_id(self) -> _uuid.UUID | None:
        if hasattr(self, "id"):
            return self.id
        return None

    def _apply(self, event: _messages.TransferEvent) -> None:
        if isinstance(event, _messages.TransferInitiatedEvent):
            self.id = event.transfer_id
            self.from_account_id = event.from_account_id
            self.to_account_id = event.to_account_id
            self.amount = event.amount
            self.status = "initial"
        elif isinstance(event, _messages.TransferWithdrawnEvent):
            self.status = "withdrawn"
        elif isinstance(event, _messages.TransferFinishedEvent):
            self.status = "finished"
        else:
            raise NotImplementedError(f"Event {type(event)} is not supported")

    @property
    def version(self) -> int:
        return self._version

    @classmethod
    def initiate(
        cls,
        transfer_id: _uuid.UUID,
        from_account_id: _uuid.UUID,
        to_account_id: _uuid.UUID,
        amount: int,
    ) -> "Transfer":
        transfer = cls()
        transfer.apply(
            _messages.TransferInitiatedEvent(
                transfer_id=transfer_id,
                from_account_id=from_account_id,
                to_account_id=to_account_id,
                amount=amount,
            )
        )
        return transfer

    def withdraw(self) -> None:
        self.apply(_messages.TransferWithdrawnEvent(transfer_id=self.id))

    def finish(self) -> None:
        self.apply(_messages.TransferFinishedEvent(transfer_id=self.id))
