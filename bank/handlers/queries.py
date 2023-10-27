import uuid as _uuid

from ..domain import Account, Transfer
from .common import AccountRepo, TransferRepo


class QueryHandler:
    """
    Offers methods to query aggregates.

    For simplicity, it returns domain objects directly. In a real application,
    you would probably want to return DTOs instead.

    It also does not use CQRS, but that is not the point of this example.
    """

    def __init__(self, account_repo: AccountRepo, transfer_repo: TransferRepo):
        self._account_repo = account_repo
        self._transfer_repo = transfer_repo

    def get_account(self, id: _uuid.UUID) -> Account:
        return self._account_repo.get(id)

    def get_transfer(self, id: _uuid.UUID) -> Transfer:
        return self._transfer_repo.get(id)
