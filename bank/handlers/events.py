from depeche_db import MessageHandler

from .. import messages as _messages
from .common import AccountCommandWiter, TransferRepo


class TransferHandler(MessageHandler[_messages.AppMessage]):
    """
    When the transfer object is changed, send commands to the accounts.
    """

    @MessageHandler.register
    def handle_transfer_initiated(
        self,
        event: _messages.TransferInitiatedEvent,
        account_command_writer: AccountCommandWiter,
    ):
        """
        Command the source account to withdraw the transfer amount
        """
        account_command_writer.write(
            account_id=event.from_account_id,
            command=_messages.WithdrawCommand(
                account_id=event.from_account_id,
                amount=event.amount,
                transfer_id=event.transfer_id,
            ),
        )

    @MessageHandler.register
    def handle_transfer_withdrawn(
        self,
        event: _messages.TransferWithdrawnEvent,
        transfer_repo: TransferRepo,
        account_command_writer: AccountCommandWiter,
    ):
        """
        Command the target account to deposit the transfer amount
        """
        transfer = transfer_repo.get(event.transfer_id)
        account_command_writer.write(
            account_id=transfer.to_account_id,
            command=_messages.DepositCommand(
                account_id=transfer.to_account_id,
                amount=transfer.amount,
                transfer_id=event.transfer_id,
            ),
        )


class AccountHandler(MessageHandler[_messages.AppMessage]):
    """
    When accounts are changed (in response to an async command sent from
    `TransferHandler`), update the transfer objects.
    """

    @MessageHandler.register
    def handle_account_withdrawn(
        self,
        event: _messages.WithdrawnEvent,
        transfer_repo: TransferRepo,
    ):
        if not event.transfer_id:
            return
        transfer = transfer_repo.get(event.transfer_id)
        current_version = transfer.version
        transfer.track_withdrawn()
        transfer_repo.save(transfer, current_version)

    @MessageHandler.register
    def handle_account_deposited(
        self,
        event: _messages.DepositedEvent,
        transfer_repo: TransferRepo,
    ):
        if not event.transfer_id:
            return
        transfer = transfer_repo.get(event.transfer_id)
        current_version = transfer.version
        transfer.track_deposited()
        transfer_repo.save(transfer, current_version)
