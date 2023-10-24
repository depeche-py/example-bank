import uuid as _uuid
from .. import domain as _domain
from .. import messages as _messages
from .. import di as _di
from .repositories import AccountRepo, TransferRepo
from depeche_db import MessageHandlerRegister


def command_handler(fn):
    fn.__command_handler__ = True
    return fn


class _CommandHandler:
    def __init__(self, container: _di.Container):
        self._container = container
        self._injector = _di.Injector(container)
        self._handlers = {}
        for name in dir(self):
            fn = getattr(self, name)
            if getattr(fn, "__command_handler__", False):
                self._handlers[fn.__annotations__["command"]] = fn

    def handle(self, command: _messages.AppMessage) -> _uuid.UUID | None:
        if type(command) in self._handlers:
            return self._injector.inject(self._handlers[type(command)], command=command)
        raise NotImplementedError(f"Command {type(command)} is not supported")


class CommandHandler(_CommandHandler):
    @command_handler
    def create_account(
        self, command: _messages.CreateAccountCommand, repo: AccountRepo
    ) -> _uuid.UUID:
        account = _domain.Account.create(
            account_id=command.account_id or _uuid.uuid4(),
            number=command.account_number,
        )
        repo.add(account)
        return account.id

    @command_handler
    def deposit(
        self, command: _messages.DepositCommand, repo: AccountRepo
    ) -> _uuid.UUID:
        account = repo.get(command.account_id)
        current_version = account.version
        account.deposit(command.amount, transfer_id=command.transfer_id)
        repo.save(account, current_version)
        return account.id

    @command_handler
    def withdraw(
        self, command: _messages.WithdrawCommand, repo: AccountRepo
    ) -> _uuid.UUID:
        account = repo.get(command.account_id)
        current_version = account.version
        account.withdraw(command.amount, transfer_id=command.transfer_id)
        repo.save(account, current_version)
        return account.id

    @command_handler
    def initiate_transfer(
        self, command: _messages.InitiateTransferCommand, repo: TransferRepo
    ) -> _uuid.UUID:
        transfer = _domain.Transfer.initiate(
            transfer_id=command.transfer_id or _uuid.uuid4(),
            from_account_id=command.from_account_id,
            to_account_id=command.to_account_id,
            amount=command.amount,
        )
        repo.add(transfer)
        return transfer.id


async_handlers = MessageHandlerRegister[_messages.AppMessage]()


@async_handlers.register
def handle_async_account_commands(
    command: _messages.DepositCommand | _messages.WithdrawCommand,
    container: _di.Container,
):
    return container.resolve(CommandHandler).handle(command)
