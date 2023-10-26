import uuid as _uuid

import explicit_di as _di
import pydantic as _pydantic
from depeche_db import MessageHandler, MessagePosition

from .. import domain as _domain
from .. import messages as _messages
from .repositories import AccountRepo, TransferRepo


class CommandResult(_pydantic.BaseModel):
    aggregate_id: _uuid.UUID
    position: MessagePosition


class CommandHandler(MessageHandler[_messages.AppMessage]):
    @MessageHandler.register
    def create_account(
        self, command: _messages.CreateAccountCommand, repo: AccountRepo
    ) -> CommandResult:
        account = _domain.Account.create(
            account_id=command.account_id or _uuid.uuid4(),
            number=command.account_number,
        )
        position = repo.add(account)
        return CommandResult(aggregate_id=account.id, position=position)

    @MessageHandler.register
    def deposit(
        self, command: _messages.DepositCommand, repo: AccountRepo
    ) -> CommandResult:
        account = repo.get(command.account_id)
        current_version = account.version
        account.deposit(command.amount, transfer_id=command.transfer_id)
        position = repo.save(account, current_version)
        return CommandResult(aggregate_id=account.id, position=position)

    @MessageHandler.register
    def withdraw(
        self, command: _messages.WithdrawCommand, repo: AccountRepo
    ) -> CommandResult:
        account = repo.get(command.account_id)
        current_version = account.version
        account.withdraw(command.amount, transfer_id=command.transfer_id)
        position = repo.save(account, current_version)
        return CommandResult(aggregate_id=account.id, position=position)

    @MessageHandler.register
    def initiate_transfer(
        self, command: _messages.InitiateTransferCommand, repo: TransferRepo
    ) -> CommandResult:
        transfer = _domain.Transfer.initiate(
            transfer_id=command.transfer_id or _uuid.uuid4(),
            from_account_id=command.from_account_id,
            to_account_id=command.to_account_id,
            amount=command.amount,
        )
        position = repo.add(transfer)
        return CommandResult(aggregate_id=transfer.id, position=position)


class CommandHandlerWithDI:
    def __init__(self, container: _di.Container):
        self.container = container
        self.register = CommandHandler()

    def handle(self, command: _messages.AppMessage) -> CommandResult:
        handler = self.register.get_handler(type(command))
        return self.container.inject(handler.handler, command=command)  # type: ignore
