from __future__ import annotations

import uuid
from django.db import models, transaction

from core.utils.coreModels import BranchScopedStampedOwnedActive, TransactionBasedBranchScopedStampedOwnedActive
from master.models import Currency

from accounting.observer.codeAssigner import assign_bank_account_code, assign_coa_code
from accounting.observer.accountManager import sync_accounts_for_coa, sync_accounts_for_bank_account, sync_accounts_for_actor
from accounting.observer.balanceUpdate import (
    handle_cashtransfer_posting,
    handle_journalvoucher_posting,
    handle_chequeregister_posting,
)


class Category(models.TextChoices):
    ASSET = "asset", "Asset"
    LIABILITY = "liability", "Liability"
    EQUITY = "equity", "Equity"
    INCOME = "income", "Income"
    EXPENSE = "expense", "Expense"


class Accounts(BranchScopedStampedOwnedActive):
    code = models.CharField(max_length=60, db_index=True)
    name = models.CharField(max_length=200)
    account_class = models.CharField(max_length=200)  # 'coa', 'bank', 'actor'
    balance = models.DecimalField(max_digits=18, decimal_places=2, default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["branch", "code"], name="uniq_accounts_code_per_branch"),
        ]

    def __str__(self):
        return f"{self.code} - {self.name}"


class Actors(BranchScopedStampedOwnedActive):
    name = models.CharField(max_length=1200)

    # ✅ each actor has its own ledger account
    account = models.OneToOneField(
        Accounts,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="actor",
    )

    def save(self, *args, **kwargs):
        sync_accounts_for_actor(self)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class ChartofAccount(BranchScopedStampedOwnedActive):
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=60, db_index=True, blank=True, default="")
    description = models.TextField(null=True, blank=True)
    parent = models.ForeignKey("self", on_delete=models.PROTECT, null=True, blank=True, related_name="children")

    # ✅ FIX: must be CharField with choices
    account_type = models.CharField(max_length=20, choices=Category.choices, default=Category.ASSET, db_index=True)

    account = models.ForeignKey(Accounts, on_delete=models.PROTECT, related_name="coa_nodes",blank=True ,null=True)
    is_group = models.BooleanField(default=False)
    is_system = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["branch", "code"], name="uniq_coa_code_per_branch"),
        ]

    def __str__(self):
        return f"{self.code} - {self.name}"

    def save(self, *args, **kwargs):
        assign_coa_code(self)
        sync_accounts_for_coa(self)
        super().save(*args, **kwargs)


class BankAccount(BranchScopedStampedOwnedActive):
    class Type(models.TextChoices):
        BANK = "bank", "Bank"
        CASH = "cash", "Cash"

    class BankAccountType(models.TextChoices):
        SAVING = "saving", "Saving"
        CURRENT = "current", "Current"

    type = models.CharField(max_length=10, choices=Type.choices, db_index=True)
    bank_name = models.CharField(max_length=150, null=True, blank=True)
    display_name = models.CharField(max_length=150)
    code = models.CharField(max_length=50, null=True, blank=True, db_index=True)

    account_name = models.CharField(max_length=150, null=True, blank=True)
    account_number = models.CharField(max_length=80, null=True, blank=True)
    account_type = models.CharField(max_length=10, choices=BankAccountType.choices, null=True, blank=True)

    currency = models.ForeignKey(Currency, on_delete=models.PROTECT, null=True, blank=True, related_name="bank_accounts")
    main_account = models.ForeignKey(
        Accounts, on_delete=models.PROTECT, null=True, blank=True, related_name="linked_bank_accounts"
    )
    description = models.TextField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["branch", "code"], name="uniq_bankaccount_code_per_branch"),
        ]

    def save(self, *args, **kwargs):
        assign_bank_account_code(self)
        sync_accounts_for_bank_account(self)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.display_name


class CashTransfer(TransactionBasedBranchScopedStampedOwnedActive):
    transfer_no = models.CharField(max_length=50, null=True, blank=True, db_index=True)
    transfer_date = models.DateField(db_index=True)
    from_account = models.ForeignKey(BankAccount, on_delete=models.PROTECT, related_name="cash_transfers_out")
    reference_no = models.CharField(max_length=80, null=True, blank=True)

    total = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    note = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.transfer_no or str(self.id)

    def save(self, *args, **kwargs):
        old = None
        if self.pk:
            old = CashTransfer.objects.only("approved", "voided_at").filter(pk=self.pk).first()

        with transaction.atomic():
            super().save(*args, **kwargs)
            handle_cashtransfer_posting(self, old_instance=old)


class CashTransferItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cash_transfer = models.ForeignKey(CashTransfer, on_delete=models.CASCADE, related_name="items")
    to_account = models.ForeignKey(BankAccount, on_delete=models.PROTECT, related_name="cash_transfers_in")
    amount = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    note = models.CharField(max_length=255, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)


class ChequeRegister(TransactionBasedBranchScopedStampedOwnedActive):
    class Status(models.TextChoices):
        ISSUED = "issued", "Issued"
        RECEIVED = "received", "Received"
        CLEARED = "cleared", "Cleared"
        BOUNCED = "bounced", "Bounced"
        CANCELLED = "cancelled", "Cancelled"

    cheque_no = models.CharField(max_length=80, null=True, blank=True, db_index=True)
    coa_account = models.ForeignKey(ChartofAccount, on_delete=models.PROTECT, null=True, blank=True, related_name="cheques")
    bank_account = models.ForeignKey(BankAccount, on_delete=models.PROTECT, null=True, blank=True, related_name="cheques")

    # ✅ now Actors
    contact = models.ForeignKey(Actors, on_delete=models.PROTECT, null=True, blank=True, related_name="cheques")

    cheque_date = models.DateField(null=True, blank=True)
    received_date = models.DateField(null=True, blank=True)

    amount = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.RECEIVED, db_index=True)
    memo = models.CharField(max_length=255, null=True, blank=True)

    total = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    note = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.cheque_no or str(self.id)

    def save(self, *args, **kwargs):
        old = None
        if self.pk:
            old = ChequeRegister.objects.only(
                "approved", "voided_at", "status", "received_date", "amount", "bank_account_id", "coa_account_id", "contact_id"
            ).filter(pk=self.pk).first()

        with transaction.atomic():
            super().save(*args, **kwargs)
            handle_chequeregister_posting(self, old_instance=old)


class JournalVoucher(TransactionBasedBranchScopedStampedOwnedActive):
    voucher_no = models.CharField(max_length=50, null=True, blank=True, db_index=True)
    voucher_date = models.DateField(db_index=True)
    narration = models.TextField(null=True, blank=True)

    total = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    note = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.voucher_no or str(self.id)

    def save(self, *args, **kwargs):
        old = None
        if self.pk:
            old = JournalVoucher.objects.only("approved", "voided_at").filter(pk=self.pk).first()

        with transaction.atomic():
            super().save(*args, **kwargs)
            handle_journalvoucher_posting(self, old_instance=old)


class JournalVoucherItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    journal_voucher = models.ForeignKey(JournalVoucher, on_delete=models.CASCADE, related_name="items")
    account = models.ForeignKey(Accounts, on_delete=models.PROTECT, related_name="journal_lines")
    dr_amount = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    cr_amount = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    line_note = models.CharField(max_length=255, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
