from __future__ import annotations

from decimal import Decimal
from django.test import TestCase
from django.utils import timezone
from django.db import models

from master.models import Branch, Currency
from accounting.models import (
    Accounts,
    Actors,
    ChartofAccount,
    BankAccount,
    CashTransfer,
    CashTransferItem,
    JournalVoucher,
    JournalVoucherItem,
    ChequeRegister,
    Category,
)


def create_minimal(Model, _depth=0, **overrides):
    """
    Creates an instance of Model by filling required fields with dummy values.
    If your Branch/Currency has special constraints, adjust overrides in setUp().
    """
    if _depth > 3:
        raise RuntimeError(f"create_minimal recursion too deep for {Model.__name__}")

    field_names = {f.name for f in Model._meta.fields}
    overrides = {k: v for k, v in overrides.items() if k in field_names}

    data = {}
    for f in Model._meta.fields:
        if f.primary_key or f.auto_created:
            continue
        if f.name in overrides:
            continue
        if f.default is not models.NOT_PROVIDED:
            continue
        if getattr(f, "null", False) or getattr(f, "blank", False):
            continue

        if isinstance(f, models.CharField):
            v = f.name.upper()
            data[f.name] = v[: (f.max_length or 20)]
        elif isinstance(f, models.TextField):
            data[f.name] = "x"
        elif isinstance(f, models.BooleanField):
            data[f.name] = True
        elif isinstance(f, models.IntegerField):
            data[f.name] = 1
        elif isinstance(f, models.DecimalField):
            data[f.name] = Decimal("1")
        elif isinstance(f, models.DateField):
            data[f.name] = timezone.now().date()
        elif isinstance(f, models.DateTimeField):
            data[f.name] = timezone.now()
        elif isinstance(f, models.ForeignKey):
            rel = f.remote_field.model
            data[f.name] = create_minimal(rel, _depth=_depth + 1)
        else:
            if getattr(f, "choices", None):
                data[f.name] = f.choices[0][0]
            else:
                data[f.name] = "x"

    data.update(overrides)
    return Model.objects.create(**data)


class AccountingObserverTests(TestCase):
    def setUp(self):
        # Try common Branch/Currency fields first; fallback to create_minimal
        try:
            self.branch = Branch.objects.create(name="Main", code="MAIN")
        except Exception:
            self.branch = create_minimal(Branch)

        try:
            self.currency = Currency.objects.create(code="NPR", name="Nepalese Rupee")
        except Exception:
            self.currency = create_minimal(Currency)

    def test_actor_gets_own_account(self):
        a = Actors.objects.create(branch=self.branch, name="Ram Bahadur")
        a.refresh_from_db()

        self.assertIsNotNone(a.account_id)
        self.assertEqual(a.account.account_class, "actor")
        self.assertTrue(a.account.code.startswith("AT"))
        self.assertEqual(a.account.balance, Decimal("0.00"))

    def test_bankaccount_code_and_main_account_created(self):
        b1 = BankAccount.objects.create(branch=self.branch, type=BankAccount.Type.BANK, display_name="Nabil", currency=self.currency)
        c1 = BankAccount.objects.create(branch=self.branch, type=BankAccount.Type.CASH, display_name="Cash Counter", currency=self.currency)

        self.assertEqual(b1.code, "BA00001")
        self.assertEqual(c1.code, "BC00001")
        self.assertIsNotNone(b1.main_account_id)
        self.assertEqual(b1.main_account.account_class, "bank")

    def test_coa_code_and_accounts_created(self):
        assets = ChartofAccount.objects.create(branch=self.branch, name="Assets", is_group=True, account_type=Category.ASSET)
        assets.refresh_from_db()
        self.assertEqual(assets.code, "1000")
        self.assertIsNotNone(assets.account_id)
        self.assertEqual(assets.account.account_class, "coa")
        self.assertEqual(assets.account.code, "1000")

        cash = ChartofAccount.objects.create(branch=self.branch, parent=assets, name="Cash", is_group=False, account_type=Category.ASSET)
        cash.refresh_from_db()
        self.assertEqual(cash.code, "1010")
        self.assertEqual(cash.account.code, "1010")

    def test_cashtransfer_post_and_reverse(self):
        from_bank = BankAccount.objects.create(branch=self.branch, type=BankAccount.Type.BANK, display_name="FromBank", currency=self.currency)
        to_bank = BankAccount.objects.create(branch=self.branch, type=BankAccount.Type.BANK, display_name="ToBank", currency=self.currency)

        ct = CashTransfer.objects.create(branch=self.branch, transfer_date=timezone.now().date(), from_account=from_bank, approved=False)
        CashTransferItem.objects.create(cash_transfer=ct, to_account=to_bank, amount=Decimal("500.00"))

        # approve -> post
        ct.approved = True
        ct.save()

        from_bank.main_account.refresh_from_db()
        to_bank.main_account.refresh_from_db()
        self.assertEqual(from_bank.main_account.balance, Decimal("-500.00"))
        self.assertEqual(to_bank.main_account.balance, Decimal("500.00"))

        # void -> reverse
        ct.voided_at = timezone.now()
        ct.save()

        from_bank.main_account.refresh_from_db()
        to_bank.main_account.refresh_from_db()
        self.assertEqual(from_bank.main_account.balance, Decimal("0.00"))
        self.assertEqual(to_bank.main_account.balance, Decimal("0.00"))

    def test_journalvoucher_post_and_reverse(self):
        a1 = Accounts.objects.create(branch=self.branch, code="A1", name="Acc1", account_class="coa", balance=0)
        a2 = Accounts.objects.create(branch=self.branch, code="A2", name="Acc2", account_class="coa", balance=0)

        jv = JournalVoucher.objects.create(branch=self.branch, voucher_date=timezone.now().date(), approved=False)
        JournalVoucherItem.objects.create(journal_voucher=jv, account=a1, dr_amount=Decimal("1000.00"), cr_amount=Decimal("0"))
        JournalVoucherItem.objects.create(journal_voucher=jv, account=a2, dr_amount=Decimal("0"), cr_amount=Decimal("1000.00"))

        jv.approved = True
        jv.save()

        a1.refresh_from_db()
        a2.refresh_from_db()
        self.assertEqual(a1.balance, Decimal("1000.00"))
        self.assertEqual(a2.balance, Decimal("-1000.00"))

        jv.voided_at = timezone.now()
        jv.save()

        a1.refresh_from_db()
        a2.refresh_from_db()
        self.assertEqual(a1.balance, Decimal("0.00"))
        self.assertEqual(a2.balance, Decimal("0.00"))

    def test_cheque_register_posts_using_actor_when_no_coa(self):
        bank = BankAccount.objects.create(branch=self.branch, type=BankAccount.Type.BANK, display_name="ChequeBank", currency=self.currency)
        actor = Actors.objects.create(branch=self.branch, name="Customer A")  # auto gets account

        cr = ChequeRegister.objects.create(
            branch=self.branch,
            cheque_no="CHQ001",
            bank_account=bank,
            contact=actor,                 # ✅ other side uses actor.account
            coa_account=None,
            amount=Decimal("200.00"),
            status=ChequeRegister.Status.RECEIVED,
            approved=False,
        )

        # clear + approve -> post
        cr.status = ChequeRegister.Status.CLEARED
        cr.approved = True
        cr.received_date = timezone.now().date()
        cr.save()

        bank.main_account.refresh_from_db()
        actor.account.refresh_from_db()
        self.assertEqual(bank.main_account.balance, Decimal("200.00"))
        self.assertEqual(actor.account.balance, Decimal("-200.00"))

        # void -> reverse
        cr.voided_at = timezone.now()
        cr.save()

        bank.main_account.refresh_from_db()
        actor.account.refresh_from_db()
        self.assertEqual(bank.main_account.balance, Decimal("0.00"))
        self.assertEqual(actor.account.balance, Decimal("0.00"))
