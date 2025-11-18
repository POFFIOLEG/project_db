from rest_framework import viewsets

from .models import (
    Contract,
    ContractItem,
    Country,
    Manufacturer,
    StorageLocation,
    Supplier,
    SupplierContact,
    Truck,
)
from .serializers import (
    ContractItemSerializer,
    ContractSerializer,
    CountrySerializer,
    ManufacturerSerializer,
    StorageLocationSerializer,
    SupplierContactSerializer,
    SupplierSerializer,
    TruckSerializer,
)


class CountryViewSet(viewsets.ModelViewSet):
    queryset = Country.objects.all()
    serializer_class = CountrySerializer


class ManufacturerViewSet(viewsets.ModelViewSet):
    queryset = Manufacturer.objects.select_related('country').all()
    serializer_class = ManufacturerSerializer


class SupplierViewSet(viewsets.ModelViewSet):
    queryset = Supplier.objects.select_related('country').prefetch_related('contacts')
    serializer_class = SupplierSerializer


class SupplierContactViewSet(viewsets.ModelViewSet):
    queryset = SupplierContact.objects.select_related('supplier').all()
    serializer_class = SupplierContactSerializer


class StorageLocationViewSet(viewsets.ModelViewSet):
    queryset = StorageLocation.objects.all()
    serializer_class = StorageLocationSerializer


class TruckViewSet(viewsets.ModelViewSet):
    queryset = Truck.objects.all()
    serializer_class = TruckSerializer


class ContractViewSet(viewsets.ModelViewSet):
    queryset = Contract.objects.select_related('supplier', 'storage_location', 'truck')
    serializer_class = ContractSerializer


class ContractItemViewSet(viewsets.ModelViewSet):
    queryset = ContractItem.objects.select_related('contract', 'product').all()
    serializer_class = ContractItemSerializer
