import datetime as _dt
import uuid as _uuid

import pydantic as _pydantic


class Message(_pydantic.BaseModel):
    message_id: _uuid.UUID = _pydantic.Field(default_factory=_uuid.uuid4)
    message_time: _dt.datetime = _pydantic.Field(default_factory=_dt.datetime.utcnow)

    def get_message_id(self) -> _uuid.UUID:
        return self.message_id

    def get_message_time(self) -> _dt.datetime:
        return self.message_time


class CreateAccountCommand(Message):
    account_id: _uuid.UUID | None = None
    account_number: str


class DepositCommand(Message):
    account_id: _uuid.UUID
    amount: int
    transfer_id: _uuid.UUID | None = None


class WithdrawCommand(Message):
    account_id: _uuid.UUID
    amount: int
    transfer_id: _uuid.UUID | None = None


class InitiateTransferCommand(Message):
    transfer_id: _uuid.UUID | None = None
    from_account_id: _uuid.UUID
    to_account_id: _uuid.UUID
    amount: int


AccountCommand = (
    CreateAccountCommand | DepositCommand | WithdrawCommand | InitiateTransferCommand
)


class AccountCreatedEvent(Message):
    account_id: _uuid.UUID
    account_number: str


class DepositedEvent(Message):
    account_id: _uuid.UUID
    amount: int
    transfer_id: _uuid.UUID | None = None


class WithdrawnEvent(Message):
    account_id: _uuid.UUID
    amount: int
    transfer_id: _uuid.UUID | None = None


class TransferInitiatedEvent(Message):
    transfer_id: _uuid.UUID
    from_account_id: _uuid.UUID
    to_account_id: _uuid.UUID
    amount: int


class TransferWithdrawnEvent(Message):
    transfer_id: _uuid.UUID


class TransferFinishedEvent(Message):
    transfer_id: _uuid.UUID


AccountEvent = AccountCreatedEvent | DepositedEvent | WithdrawnEvent
TransferEvent = TransferInitiatedEvent | TransferWithdrawnEvent | TransferFinishedEvent

AppMessage = AccountCommand | AccountEvent | TransferEvent
