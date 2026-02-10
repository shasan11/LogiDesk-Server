from core.utils.AdaptedBulkListSerializer import BulkModelSerializer
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


class UnitofMeasurementSerializer(BulkModelSerializer):
    class Meta:
        model = UnitofMeasurement
        fields = "__all__"


class UnitofMeasurementLengthSerializer(BulkModelSerializer):
    class Meta:
        model = UnitofMeasurementLength
        fields = "__all__"


class PortsSerializer(BulkModelSerializer):
    class Meta:
        model = Ports
        fields = "__all__"


class BranchSerializer(BulkModelSerializer):
    class Meta:
        model = Branch
        fields = "__all__"


class MasterDataSerializer(BulkModelSerializer):
    class Meta:
        model = MasterData
        fields = "__all__"


class ApplicationSettingsSerializer(BulkModelSerializer):
    class Meta:
        model = ApplicationSettings
        fields = "__all__"


class ShipmentPrefixesSerializer(BulkModelSerializer):
    class Meta:
        model = ShipmentPrefixes
        fields = "__all__"


class CurrencySerializer(BulkModelSerializer):
    class Meta:
        model = Currency
        fields = "__all__"
