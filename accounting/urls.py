from django.urls import include, path
from rest_framework_bulk.routes import BulkRouter

from accounting.views import (
    AccountsViewSet,
    AccountingActorViewSet,
    BankAccountViewSet,
    CashTransferItemViewSet,
    CashTransferViewSet,
    ChartofAccountViewSet,
    ChequeRegisterViewSet,
    JournalVoucherItemViewSet,
    JournalVoucherViewSet,
)

router = BulkRouter()
router.register(r"accounts", AccountsViewSet, basename="accounts")
router.register(r"actors", AccountingActorViewSet, basename="accounting-actor")
router.register(r"chart-of-accounts", ChartofAccountViewSet, basename="chart-of-account")
router.register(r"bank-accounts", BankAccountViewSet, basename="bank-account")
router.register(r"cash-transfers", CashTransferViewSet, basename="cash-transfer")
router.register(r"cash-transfer-items", CashTransferItemViewSet, basename="cash-transfer-item")
router.register(r"cheque-registers", ChequeRegisterViewSet, basename="cheque-register")
router.register(r"journal-vouchers", JournalVoucherViewSet, basename="journal-voucher")
router.register(r"journal-voucher-items", JournalVoucherItemViewSet, basename="journal-voucher-item")

urlpatterns = [
    path("", include(router.urls)),
]
