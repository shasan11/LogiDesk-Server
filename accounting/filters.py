# accounting/filters.py
import django_filters
from django_filters import rest_framework as filters

from accounting.models import (
    Accounts,
    Actors,
    BankAccount,
    CashTransfer,
    CashTransferItem,
    ChartofAccount,
    ChequeRegister,
    JournalVoucher,
    JournalVoucherItem,
)

class AccountsFilter(filters.FilterSet):
    q = filters.CharFilter(method="filter_q")
    active = filters.BooleanFilter(field_name="active")
    is_active = filters.BooleanFilter(field_name="active")  # alias

    def filter_q(self, qs, name, value):
        return qs.filter(name__icontains=value) | qs.filter(code__icontains=value)

    class Meta:
        model = Accounts
        fields = ["branch", "account_class", "active", "is_active", "q"]


class AccountingActorFilter(filters.FilterSet):
    q = filters.CharFilter(method="filter_q")
    active = filters.BooleanFilter(field_name="active")
    is_active = filters.BooleanFilter(field_name="active")

    def filter_q(self, qs, name, value):
        return qs.filter(name__icontains=value)

    class Meta:
        model = Actors
        fields = ["branch", "active", "is_active", "q"]


class ChartofAccountFilter(filters.FilterSet):
    q = filters.CharFilter(method="filter_q")
    active = filters.BooleanFilter(field_name="active")
    is_active = filters.BooleanFilter(field_name="active")

    def filter_q(self, qs, name, value):
        return qs.filter(name__icontains=value) | qs.filter(code__icontains=value)

    class Meta:
        model = ChartofAccount
        fields = [
            "branch",
            "account_type",
            "is_group",
            "is_system",
            "parent",
            "active",
            "is_active",
            "q",
        ]


class BankAccountFilter(filters.FilterSet):
    q = filters.CharFilter(method="filter_q")
    active = filters.BooleanFilter(field_name="active")
    is_active = filters.BooleanFilter(field_name="active")

    def filter_q(self, qs, name, value):
        return (
            qs.filter(display_name__icontains=value)
            | qs.filter(bank_name__icontains=value)
            | qs.filter(account_number__icontains=value)
            | qs.filter(code__icontains=value)
        )

    class Meta:
        model = BankAccount
        fields = ["branch", "type", "currency", "active", "is_active", "q"]


class CashTransferFilter(filters.FilterSet):
    q = filters.CharFilter(method="filter_q")
    active = filters.BooleanFilter(field_name="active")
    is_active = filters.BooleanFilter(field_name="active")

    def filter_q(self, qs, name, value):
        return qs.filter(transfer_no__icontains=value) | qs.filter(reference_no__icontains=value)

    class Meta:
        model = CashTransfer
        fields = ["branch", "transfer_date", "from_account", "active", "is_active", "q"]


class CashTransferItemFilter(filters.FilterSet):
    q = filters.CharFilter(field_name="note", lookup_expr="icontains")

    class Meta:
        model = CashTransferItem
        fields = ["cash_transfer", "to_account", "q"]


class ChequeRegisterFilter(filters.FilterSet):
    q = filters.CharFilter(method="filter_q")
    active = filters.BooleanFilter(field_name="active")
    is_active = filters.BooleanFilter(field_name="active")

    def filter_q(self, qs, name, value):
        return qs.filter(cheque_no__icontains=value) | qs.filter(memo__icontains=value)

    class Meta:
        model = ChequeRegister
        fields = [
            "branch",
            "status",
            "cheque_date",
            "received_date",
            "bank_account",
            "coa_account",
            "contact",
            "active",
            "is_active",
            "q",
        ]


class JournalVoucherFilter(filters.FilterSet):
    q = filters.CharFilter(method="filter_q")
    active = filters.BooleanFilter(field_name="active")
    is_active = filters.BooleanFilter(field_name="active")

    def filter_q(self, qs, name, value):
        return qs.filter(voucher_no__icontains=value)

    class Meta:
        model = JournalVoucher
        fields = ["branch", "voucher_date", "active", "is_active", "q"]


class JournalVoucherItemFilter(filters.FilterSet):
    q = filters.CharFilter(field_name="line_note", lookup_expr="icontains")

    class Meta:
        model = JournalVoucherItem
        fields = ["journal_voucher", "account", "q"]
