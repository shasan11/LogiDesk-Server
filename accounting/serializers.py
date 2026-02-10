from __future__ import annotations

from rest_framework import serializers

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
from core.utils.AdaptedBulkListSerializer import BulkModelSerializer


class AccountsSerializer(BulkModelSerializer):
    class Meta:
        model = Accounts
        fields = "__all__"


class AccountingActorSerializer(BulkModelSerializer):
    class Meta:
        model = Actors
        fields = "__all__"


class ChartofAccountSerializer(BulkModelSerializer):
    class Meta:
        model = ChartofAccount
        fields = "__all__"


class BankAccountSerializer(BulkModelSerializer):
    class Meta:
        model = BankAccount
        fields = "__all__"


class CashTransferItemSerializer(BulkModelSerializer):
    class Meta:
        model = CashTransferItem
        fields = "__all__"


class CashTransferSerializer(BulkModelSerializer):
    items = CashTransferItemSerializer(many=True, required=False)

    class Meta:
        model = CashTransfer
        fields = "__all__"

    def create(self, validated_data):
        items_data = validated_data.pop("items", [])
        obj = super().create(validated_data)
        for item in items_data:
            CashTransferItem.objects.create(cash_transfer=obj, **item)
        return obj

    def update(self, instance, validated_data):
        items_data = validated_data.pop("items", None)
        obj = super().update(instance, validated_data)
        if items_data is not None:
            obj.items.all().delete()
            for item in items_data:
                CashTransferItem.objects.create(cash_transfer=obj, **item)
        return obj


class ChequeRegisterSerializer(BulkModelSerializer):
    class Meta:
        model = ChequeRegister
        fields = "__all__"


class JournalVoucherItemSerializer(BulkModelSerializer):
    class Meta:
        model = JournalVoucherItem
        fields = "__all__"


class JournalVoucherSerializer(BulkModelSerializer):
    items = JournalVoucherItemSerializer(many=True, required=False)

    class Meta:
        model = JournalVoucher
        fields = "__all__"

    def create(self, validated_data):
        items_data = validated_data.pop("items", [])
        obj = super().create(validated_data)
        for item in items_data:
            JournalVoucherItem.objects.create(journal_voucher=obj, **item)
        return obj

    def update(self, instance, validated_data):
        items_data = validated_data.pop("items", None)
        obj = super().update(instance, validated_data)
        if items_data is not None:
            obj.items.all().delete()
            for item in items_data:
                JournalVoucherItem.objects.create(journal_voucher=obj, **item)
        return obj
