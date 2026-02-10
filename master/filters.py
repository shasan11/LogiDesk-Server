import django_filters

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


class UnitofMeasurementFilter(django_filters.FilterSet):
    q = django_filters.CharFilter(method="filter_q")

    def filter_q(self, queryset, name, value):
        return queryset.filter(name__icontains=value) | queryset.filter(symbol__icontains=value)

    class Meta:
        model = UnitofMeasurement
        fields = ["active", "q"]


class UnitofMeasurementLengthFilter(django_filters.FilterSet):
    q = django_filters.CharFilter(method="filter_q")

    def filter_q(self, queryset, name, value):
        return queryset.filter(name__icontains=value) | queryset.filter(symbol__icontains=value)

    class Meta:
        model = UnitofMeasurementLength
        fields = ["active", "q"]


class PortsFilter(django_filters.FilterSet):
    q = django_filters.CharFilter(method="filter_q")

    def filter_q(self, queryset, name, value):
        return (
            queryset.filter(name__icontains=value)
            | queryset.filter(symbol__icontains=value)
            | queryset.filter(iso__icontains=value)
            | queryset.filter(iata__icontains=value)
            | queryset.filter(edi__icontains=value)
            | queryset.filter(city__icontains=value)
            | queryset.filter(country__icontains=value)
            | queryset.filter(region__icontains=value)
        )

    class Meta:
        model = Ports
        fields = ["active", "is_land", "is_air", "is_sea", "nearest_branch", "country", "city", "q"]


class BranchFilter(django_filters.FilterSet):
    q = django_filters.CharFilter(method="filter_q")

    def filter_q(self, queryset, name, value):
        return (
            queryset.filter(name__icontains=value)
            | queryset.filter(branch_id__icontains=value)
            | queryset.filter(city__icontains=value)
            | queryset.filter(country__icontains=value)
            | queryset.filter(contact_number__icontains=value)
        )

    class Meta:
        model = Branch
        fields = ["active", "status", "is_main_branch", "city", "country", "q"]


class MasterDataFilter(django_filters.FilterSet):
    q = django_filters.CharFilter(method="filter_q")

    def filter_q(self, queryset, name, value):
        return queryset.filter(name__icontains=value) | queryset.filter(description__icontains=value)

    class Meta:
        model = MasterData
        fields = ["type_master", "active", "q"]


class ApplicationSettingsFilter(django_filters.FilterSet):
    q = django_filters.CharFilter(method="filter_q")

    def filter_q(self, queryset, name, value):
        return (
            queryset.filter(name__icontains=value)
            | queryset.filter(country__icontains=value)
            | queryset.filter(state__icontains=value)
            | queryset.filter(email__icontains=value)
            | queryset.filter(phone__icontains=value)
        )

    class Meta:
        model = ApplicationSettings
        fields = ["country", "state", "q"]


class ShipmentPrefixesFilter(django_filters.FilterSet):
    q = django_filters.CharFilter(method="filter_q")

    def filter_q(self, queryset, name, value):
        return (
            queryset.filter(shipment_prefix__icontains=value)
            | queryset.filter(master_job_prefix__icontains=value)
            | queryset.filter(booking_prefix__icontains=value)
            | queryset.filter(order_number_prefix__icontains=value)
            | queryset.filter(sales_prefix__icontains=value)
        )

    class Meta:
        model = ShipmentPrefixes
        fields = ["q"]


class CurrencyFilter(django_filters.FilterSet):
    q = django_filters.CharFilter(method="filter_q")

    def filter_q(self, queryset, name, value):
        return (
            queryset.filter(name__icontains=value)
            | queryset.filter(code__icontains=value)
            | queryset.filter(symbol__icontains=value)
        )

    class Meta:
        model = Currency
        fields = ["active", "is_base", "code", "q"]
