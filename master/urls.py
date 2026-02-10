from django.urls import include, path
from rest_framework_bulk.routes import BulkRouter

from master.views import (
    ApplicationSettingsViewSet,
    BranchViewSet,
    CurrencyViewSet,
    MasterDataViewSet,
    PortsViewSet,
    ShipmentPrefixesViewSet,
    UnitofMeasurementLengthViewSet,
    UnitofMeasurementViewSet,
)

router = BulkRouter()
router.register(r"units", UnitofMeasurementViewSet, basename="unit-of-measurement")
router.register(r"length-units", UnitofMeasurementLengthViewSet, basename="unit-of-measurement-length")
router.register(r"ports", PortsViewSet, basename="ports")
router.register(r"branches", BranchViewSet, basename="branch")
router.register(r"master-data", MasterDataViewSet, basename="master-data")
router.register(r"application-settings", ApplicationSettingsViewSet, basename="application-settings")
router.register(r"shipment-prefixes", ShipmentPrefixesViewSet, basename="shipment-prefixes")
router.register(r"currencies", CurrencyViewSet, basename="currency")

urlpatterns = [
    path("", include(router.urls)),
]
