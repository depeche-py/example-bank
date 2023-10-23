from depeche_db import MessageStore
from .. import messages as _messages
from . import repositories


def handle_transfer_initiated(
    event: _messages.TransferInitiatedEvent,
    message_store: MessageStore[_messages.AppMessage],
):
    """
    Command the source account to withdraw the transfer amount
    """
    # TODO abstract this
    message_store.write(
        f"account-command-{event.from_account_id}",
        _messages.WithdrawCommand(
            account_id=event.from_account_id,
            amount=event.amount,
            transfer_id=event.transfer_id,
        ),
    )


def handle_account_withdrawn(
    event: _messages.WithdrawnEvent,
    transfer_repo: repositories.TransferRepo,
):
    if not event.transfer_id:
        return
    transfer = transfer_repo.get(event.transfer_id)
    current_version = transfer.version
    transfer.withdraw()
    transfer_repo.save(transfer, current_version)


def handle_transfer_withdrawn(
    event: _messages.TransferWithdrawnEvent,
    transfer_repo: repositories.TransferRepo,
    message_store: MessageStore[_messages.AppMessage],
):
    """
    Command the target account to deposit the transfer amount
    """
    transfer = transfer_repo.get(event.transfer_id)
    # TODO abstract this
    message_store.write(
        f"account-command-{transfer.to_account_id}",
        _messages.DepositCommand(
            account_id=transfer.to_account_id,
            amount=transfer.amount,
            transfer_id=event.transfer_id,
        ),
    )


def handle_account_deposited(
    event: _messages.DepositedEvent,
    transfer_repo: repositories.TransferRepo,
):
    if not event.transfer_id:
        return
    transfer = transfer_repo.get(event.transfer_id)
    current_version = transfer.version
    transfer.finish()
    transfer_repo.save(transfer, current_version)
