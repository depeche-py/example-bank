import fastapi as _fastapi
import uuid as _uuid
from ._base import app, command_handler, query_handler
from ..handlers.commands import CommandHandler
from ..handlers.queries import QueryHandler
from .. import messages as _messages
import pydantic as _pydantic


class AccountInput(_pydantic.BaseModel):
    account_number: str


class Account(_pydantic.BaseModel):
    model_config = _pydantic.ConfigDict(from_attributes=True)

    id: _uuid.UUID
    number: str
    balance: int
    version: int


@app.post("/account")
def create_account(
    account: AccountInput,
    commands: CommandHandler = command_handler,
    query: QueryHandler = query_handler,
) -> Account:
    account_id = commands.handle(
        _messages.CreateAccountCommand(account_number=account.account_number)
    )
    return Account.model_validate(query.get_account(account_id))


@app.get("/account/{account_id}")
def get_account(
    account_id: _uuid.UUID,
    query: QueryHandler = query_handler,
) -> Account:
    return Account.model_validate(query.get_account(account_id))


@app.post("/account/{account_id}/deposit")
def deposit(
    account_id: _uuid.UUID,
    amount: int = _fastapi.Body(..., embed=True),
    commands: CommandHandler = command_handler,
    query: QueryHandler = query_handler,
):
    commands.handle(_messages.DepositCommand(account_id=account_id, amount=amount))
    return "OK"


@app.post("/account/{account_id}/withdraw")
def withdraw(
    account_id: _uuid.UUID,
    amount: int = _fastapi.Body(..., embed=True),
    commands: CommandHandler = command_handler,
    query: QueryHandler = query_handler,
):
    commands.handle(_messages.WithdrawCommand(account_id=account_id, amount=amount))
    return "OK"