from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter

from accounting.filters import (
    AccountsFilter,
    AccountingActorFilter,
    BankAccountFilter,
    CashTransferFilter,
    CashTransferItemFilter,
    ChartofAccountFilter,
    ChequeRegisterFilter,
    JournalVoucherFilter,
    JournalVoucherItemFilter,
)
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
from accounting.serializers import (
    AccountsSerializer,
    AccountingActorSerializer,
    BankAccountSerializer,
    CashTransferItemSerializer,
    CashTransferSerializer,
    ChartofAccountSerializer,
    ChequeRegisterSerializer,
    JournalVoucherItemSerializer,
    JournalVoucherSerializer,
)
from core.utils.BaseModelViewSet import BaseModelViewSet


class AccountsViewSet(BaseModelViewSet):
    queryset = Accounts.objects.all()
    serializer_class = AccountsSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = AccountsFilter
    search_fields = ["name", "code"]
    ordering_fields = ["name", "code", "created"]


class AccountingActorViewSet(BaseModelViewSet):
    queryset = Actors.objects.all().select_related("account")
    serializer_class = AccountingActorSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = AccountingActorFilter
    search_fields = ["name"]
    ordering_fields = ["name", "created"]


class ChartofAccountViewSet(BaseModelViewSet):
    queryset = ChartofAccount.objects.all().select_related("parent", "account")
    serializer_class = ChartofAccountSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ChartofAccountFilter
    search_fields = ["name", "code"]
    ordering_fields = ["name", "code", "created"]


class BankAccountViewSet(BaseModelViewSet):
    queryset = BankAccount.objects.all().select_related("currency", "main_account")
    serializer_class = BankAccountSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = BankAccountFilter
    search_fields = ["display_name", "bank_name", "account_number", "code"]
    ordering_fields = ["display_name", "bank_name", "created"]


class CashTransferViewSet(BaseModelViewSet):
    queryset = CashTransfer.objects.all().select_related("from_account").prefetch_related("items", "items__to_account")
    serializer_class = CashTransferSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = CashTransferFilter
    search_fields = ["transfer_no", "reference_no"]
    ordering_fields = ["transfer_date", "created"]


class CashTransferItemViewSet(BaseModelViewSet):
    queryset = CashTransferItem.objects.all().select_related("cash_transfer", "to_account")
    serializer_class = CashTransferItemSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = CashTransferItemFilter
    search_fields = ["note"]
    ordering_fields = ["created", "amount"]


class ChequeRegisterViewSet(BaseModelViewSet):
    queryset = ChequeRegister.objects.all().select_related("coa_account", "bank_account", "contact")
    serializer_class = ChequeRegisterSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ChequeRegisterFilter
    search_fields = ["cheque_no", "memo"]
    ordering_fields = ["cheque_date", "received_date", "created"]


class JournalVoucherViewSet(BaseModelViewSet):
    queryset = JournalVoucher.objects.all().prefetch_related("items", "items__account")
    serializer_class = JournalVoucherSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = JournalVoucherFilter
    search_fields = ["voucher_no"]
    ordering_fields = ["voucher_date", "created"]


class JournalVoucherItemViewSet(BaseModelViewSet):
    queryset = JournalVoucherItem.objects.all().select_related("journal_voucher", "account")
    serializer_class = JournalVoucherItemSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = JournalVoucherItemFilter
    search_fields = ["line_note"]
    ordering_fields = ["created", "dr_amount", "cr_amount"]
