import django_filters

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


class AccountsFilter(django_filters.FilterSet):
    q = django_filters.CharFilter(method="filter_q")

    def filter_q(self, qs, name, value):
        return qs.filter(name__icontains=value) | qs.filter(code__icontains=value)

    class Meta:
        model = Accounts
        fields = ["branch", "account_class", "q"]


class AccountingActorFilter(django_filters.FilterSet):
    q = django_filters.CharFilter(method="filter_q")

    def filter_q(self, qs, name, value):
        return qs.filter(name__icontains=value)

    class Meta:
        model = Actors
        fields = ["branch", "q"]


class ChartofAccountFilter(django_filters.FilterSet):
    q = django_filters.CharFilter(method="filter_q")

    def filter_q(self, qs, name, value):
        return qs.filter(name__icontains=value) | qs.filter(code__icontains=value)

    class Meta:
        model = ChartofAccount
        fields = ["branch", "account_type", "is_group", "is_system", "parent", "q"]


class BankAccountFilter(django_filters.FilterSet):
    q = django_filters.CharFilter(method="filter_q")

    def filter_q(self, qs, name, value):
        return (
            qs.filter(display_name__icontains=value)
            | qs.filter(bank_name__icontains=value)
            | qs.filter(account_number__icontains=value)
            | qs.filter(code__icontains=value)
        )

    class Meta:
        model = BankAccount
        fields = ["branch", "type", "currency", "q"]


class CashTransferFilter(django_filters.FilterSet):
    q = django_filters.CharFilter(method="filter_q")

    def filter_q(self, qs, name, value):
        return qs.filter(transfer_no__icontains=value) | qs.filter(reference_no__icontains=value)

    class Meta:
        model = CashTransfer
        fields = ["branch", "transfer_date", "from_account", "q"]


class CashTransferItemFilter(django_filters.FilterSet):
    q = django_filters.CharFilter(field_name="note", lookup_expr="icontains")

    class Meta:
        model = CashTransferItem
        fields = ["cash_transfer", "to_account", "q"]


class ChequeRegisterFilter(django_filters.FilterSet):
    q = django_filters.CharFilter(method="filter_q")

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
            "q",
        ]


class JournalVoucherFilter(django_filters.FilterSet):
    q = django_filters.CharFilter(method="filter_q")

    def filter_q(self, qs, name, value):
        return qs.filter(voucher_no__icontains=value)

    class Meta:
        model = JournalVoucher
        fields = ["branch", "voucher_date", "q"]


class JournalVoucherItemFilter(django_filters.FilterSet):
    q = django_filters.CharFilter(field_name="line_note", lookup_expr="icontains")

    class Meta:
        model = JournalVoucherItem
        fields = ["journal_voucher", "account", "q"]
