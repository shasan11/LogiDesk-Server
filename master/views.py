from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework_bulk.generics import BulkModelViewSet

from master.filters import (
    ApplicationSettingsFilter,
    BranchFilter,
    CurrencyFilter,
    MasterDataFilter,
    PortsFilter,
    ShipmentPrefixesFilter,
    UnitofMeasurementFilter,
    UnitofMeasurementLengthFilter,
)
from master.models import (
    ApplicationSettings,
    Branch,
    Currency,
    MasterData,
    Ports,
    ShipmentPrefixes,
    UnitofMeasurement,
    UnitofMeasurementLength,
)
from master.serializers import (
    ApplicationSettingsSerializer,
    BranchSerializer,
    CurrencySerializer,
    MasterDataSerializer,
    PortsSerializer,
    ShipmentPrefixesSerializer,
    UnitofMeasurementLengthSerializer,
    UnitofMeasurementSerializer,
)


class MasterBaseViewSet(BulkModelViewSet):
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]


class UnitofMeasurementViewSet(MasterBaseViewSet):
    queryset = UnitofMeasurement.objects.all()
    serializer_class = UnitofMeasurementSerializer
    filterset_class = UnitofMeasurementFilter
    search_fields = ["name", "symbol"]
    ordering_fields = ["name", "symbol", "created", "updated_at"]


class UnitofMeasurementLengthViewSet(MasterBaseViewSet):
    queryset = UnitofMeasurementLength.objects.all()
    serializer_class = UnitofMeasurementLengthSerializer
    filterset_class = UnitofMeasurementLengthFilter
    search_fields = ["name", "symbol"]
    ordering_fields = ["name", "symbol", "created", "updated_at"]


class PortsViewSet(MasterBaseViewSet):
    queryset = Ports.objects.select_related("nearest_branch", "added_by").all()
    serializer_class = PortsSerializer
    filterset_class = PortsFilter
    search_fields = ["name", "symbol", "iso", "iata", "edi", "city", "country", "region"]
    ordering_fields = ["name", "symbol", "country", "city", "created", "updated_at"]


class BranchViewSet(MasterBaseViewSet):
    queryset = Branch.objects.select_related("added_by").all()
    serializer_class = BranchSerializer
    filterset_class = BranchFilter
    search_fields = ["name", "branch_id", "city", "country", "contact_number"]
    ordering_fields = ["name", "branch_id", "city", "country", "status", "created", "updated_at"]


class MasterDataViewSet(MasterBaseViewSet):
    queryset = MasterData.objects.all()
    serializer_class = MasterDataSerializer
    filterset_class = MasterDataFilter
    search_fields = ["type_master", "name", "description"]
    ordering_fields = ["type_master", "name"]


class ApplicationSettingsViewSet(MasterBaseViewSet):
    queryset = ApplicationSettings.objects.all()
    serializer_class = ApplicationSettingsSerializer
    filterset_class = ApplicationSettingsFilter
    search_fields = ["name", "country", "state", "email", "phone"]
    ordering_fields = ["name", "country", "state"]


class ShipmentPrefixesViewSet(MasterBaseViewSet):
    queryset = ShipmentPrefixes.objects.all()
    serializer_class = ShipmentPrefixesSerializer
    filterset_class = ShipmentPrefixesFilter
    search_fields = [
        "shipment_prefix",
        "journal_voucher_prefix",
        "sales_prefix",
        "master_job_prefix",
        "booking_prefix",
        "order_number_prefix",
    ]
    ordering_fields = ["shipment_prefix", "sales_prefix", "master_job_prefix", "booking_prefix"]


class CurrencyViewSet(MasterBaseViewSet):
    queryset = Currency.objects.select_related("user_add").all()
    serializer_class = CurrencySerializer
    filterset_class = CurrencyFilter
    search_fields = ["name", "code", "symbol"]
    ordering_fields = ["name", "code", "rate_to_base", "created", "updated"]
