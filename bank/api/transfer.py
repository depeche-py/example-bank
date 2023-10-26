import uuid as _uuid

import pydantic as _pydantic

from .. import messages as _messages
from ..handlers.commands import CommandHandlerWithDI
from ..handlers.queries import QueryHandler
from ._base import app, command_handler, query_handler


class TransferIn(_pydantic.BaseModel):
    from_account_id: _uuid.UUID
    to_account_id: _uuid.UUID
    amount: int


class Transfer(_pydantic.BaseModel):
    model_config = _pydantic.ConfigDict(from_attributes=True)

    from_account_id: _uuid.UUID
    to_account_id: _uuid.UUID
    amount: int

    status: str


@app.post("/transfer")
def initiate_transfer(
    transfer: TransferIn,
    commands: CommandHandlerWithDI = command_handler,
    query: QueryHandler = query_handler,
) -> Transfer:
    transfer_id = commands.handle(
        _messages.InitiateTransferCommand(
            from_account_id=transfer.from_account_id,
            to_account_id=transfer.to_account_id,
            amount=transfer.amount,
        )
    )
    return Transfer.model_validate(query.get_transfer(transfer_id))
