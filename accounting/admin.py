from django.contrib import admin
from django.db.models import Sum

from unfold.admin import ModelAdmin, TabularInline

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


@admin.action(description="Mark selected records as active")
def make_active(modeladmin, request, queryset):
    queryset.update(active=True)


@admin.action(description="Mark selected records as inactive")
def make_inactive(modeladmin, request, queryset):
    queryset.update(active=False)


@admin.action(description="Mark selected records as approved")
def mark_approved(modeladmin, request, queryset):
    queryset.update(approved=True)


@admin.action(description="Mark selected records as unapproved")
def mark_unapproved(modeladmin, request, queryset):
    queryset.update(approved=False)


class BranchScopedAdminMixin(ModelAdmin):
    actions = (make_active, make_inactive)
    list_filter = ("branch", "active", "is_system_generated", "created")
    readonly_fields = ("created", "updated", "user_add", "is_system_generated")
    list_per_page = 25
    ordering = ("-created",)


class TransactionInlineMixin(TabularInline):
    extra = 1
    classes = ("collapse",)


@admin.register(Accounts)
class AccountsAdmin(BranchScopedAdminMixin):
    list_display = ("code", "name", "account_class", "balance", "branch", "active", "created")
    search_fields = ("code", "name", "account_class")
    list_filter = BranchScopedAdminMixin.list_filter + ("account_class",)
    readonly_fields = BranchScopedAdminMixin.readonly_fields + ("balance",)


@admin.register(Actors)
class ActorsAdmin(BranchScopedAdminMixin):
    list_display = ("name", "account", "branch", "active", "created")
    search_fields = ("name", "account__name", "account__code")
    autocomplete_fields = ("account",)


@admin.register(ChartofAccount)
class ChartofAccountAdmin(BranchScopedAdminMixin):
    list_display = (
        "code",
        "name",
        "account_type",
        "parent",
        "account",
        "is_group",
        "is_system",
        "branch",
        "active",
    )
    search_fields = ("code", "name", "description", "account__name", "account__code")
    list_filter = BranchScopedAdminMixin.list_filter + ("account_type", "is_group", "is_system")
    autocomplete_fields = ("parent", "account")


@admin.register(BankAccount)
class BankAccountAdmin(BranchScopedAdminMixin):
    list_display = (
        "display_name",
        "code",
        "type",
        "bank_name",
        "account_number",
        "account_type",
        "currency",
        "main_account",
        "branch",
        "active",
    )
    search_fields = (
        "display_name",
        "code",
        "bank_name",
        "account_name",
        "account_number",
        "main_account__name",
        "main_account__code",
    )
    list_filter = BranchScopedAdminMixin.list_filter + ("type", "account_type", "currency")
    autocomplete_fields = ("currency", "main_account")


class CashTransferItemInline(TransactionInlineMixin):
    model = CashTransferItem
    autocomplete_fields = ("to_account",)
    fields = ("to_account", "amount", "note")


@admin.register(CashTransfer)
class CashTransferAdmin(BranchScopedAdminMixin):
    actions = BranchScopedAdminMixin.actions + (mark_approved, mark_unapproved)
    inlines = (CashTransferItemInline,)
    list_display = (
        "transfer_no",
        "transfer_date",
        "from_account",
        "total",
        "items_total",
        "approved",
        "voided_at",
        "branch",
        "active",
    )
    search_fields = ("transfer_no", "reference_no", "note", "from_account__display_name", "from_account__code")
    list_filter = BranchScopedAdminMixin.list_filter + ("approved", "transfer_date")
    autocomplete_fields = ("from_account", "approved_by")
    readonly_fields = BranchScopedAdminMixin.readonly_fields + ("approved_at", "voided_at")
    date_hierarchy = "transfer_date"

    @admin.display(description="Items Total")
    def items_total(self, obj):
        return obj.items.aggregate(total=Sum("amount")).get("total") or 0


@admin.register(CashTransferItem)
class CashTransferItemAdmin(ModelAdmin):
    list_display = ("cash_transfer", "to_account", "amount", "created")
    search_fields = ("cash_transfer__transfer_no", "to_account__display_name", "note")
    autocomplete_fields = ("cash_transfer", "to_account")
    readonly_fields = ("created", "updated")
    ordering = ("-created",)


@admin.register(ChequeRegister)
class ChequeRegisterAdmin(BranchScopedAdminMixin):
    actions = BranchScopedAdminMixin.actions + (mark_approved, mark_unapproved)
    list_display = (
        "cheque_no",
        "status",
        "bank_account",
        "coa_account",
        "contact",
        "amount",
        "cheque_date",
        "received_date",
        "approved",
        "branch",
        "active",
    )
    search_fields = ("cheque_no", "memo", "note", "bank_account__display_name", "coa_account__name", "contact__name")
    list_filter = BranchScopedAdminMixin.list_filter + ("status", "approved", "cheque_date", "received_date")
    autocomplete_fields = ("coa_account", "bank_account", "contact", "approved_by")
    readonly_fields = BranchScopedAdminMixin.readonly_fields + ("approved_at", "voided_at")
    date_hierarchy = "cheque_date"


class JournalVoucherItemInline(TransactionInlineMixin):
    model = JournalVoucherItem
    autocomplete_fields = ("account",)
    fields = ("account", "dr_amount", "cr_amount", "line_note")


@admin.register(JournalVoucher)
class JournalVoucherAdmin(BranchScopedAdminMixin):
    actions = BranchScopedAdminMixin.actions + (mark_approved, mark_unapproved)
    inlines = (JournalVoucherItemInline,)
    list_display = (
        "voucher_no",
        "voucher_date",
        "total",
        "debit_total",
        "credit_total",
        "approved",
        "voided_at",
        "branch",
        "active",
    )
    search_fields = ("voucher_no", "narration", "note")
    list_filter = BranchScopedAdminMixin.list_filter + ("approved", "voucher_date")
    autocomplete_fields = ("approved_by",)
    readonly_fields = BranchScopedAdminMixin.readonly_fields + ("approved_at", "voided_at")
    date_hierarchy = "voucher_date"

    @admin.display(description="Debit")
    def debit_total(self, obj):
        return obj.items.aggregate(total=Sum("dr_amount")).get("total") or 0

    @admin.display(description="Credit")
    def credit_total(self, obj):
        return obj.items.aggregate(total=Sum("cr_amount")).get("total") or 0


@admin.register(JournalVoucherItem)
class JournalVoucherItemAdmin(ModelAdmin):
    list_display = ("journal_voucher", "account", "dr_amount", "cr_amount", "created")
    search_fields = ("journal_voucher__voucher_no", "account__name", "account__code", "line_note")
    autocomplete_fields = ("journal_voucher", "account")
    readonly_fields = ("created", "updated")
    ordering = ("-created",)
