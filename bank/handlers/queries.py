import uuid as _uuid

from ..domain import Account, Transfer
from .repositories import AccountRepo, TransferRepo


class QueryHandler:
    def __init__(self, account_repo: AccountRepo, transfer_repo: TransferRepo):
        self._account_repo = account_repo
        self._transfer_repo = transfer_repo

    def get_account(self, id: _uuid.UUID) -> Account:
        return self._account_repo.get(id)

    def get_transfer(self, id: _uuid.UUID) -> Transfer:
        return self._transfer_repo.get(id)
