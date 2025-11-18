from rest_framework import serializers

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


class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = '__all__'


class ManufacturerSerializer(serializers.ModelSerializer):
    country = CountrySerializer(read_only=True)
    country_id = serializers.PrimaryKeyRelatedField(
        queryset=Country.objects.all(), write_only=True, source='country'
    )

    class Meta:
        model = Manufacturer
        fields = ['id', 'name', 'company_code', 'country', 'country_id', 'created_at', 'updated_at']


class SupplierContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupplierContact
        fields = '__all__'


class SupplierSerializer(serializers.ModelSerializer):
    country = CountrySerializer(read_only=True)
    country_id = serializers.PrimaryKeyRelatedField(
        queryset=Country.objects.all(), write_only=True, source='country'
    )
    contacts = SupplierContactSerializer(many=True, read_only=True)

    class Meta:
        model = Supplier
        fields = [
            'id',
            'name',
            'tax_number',
            'address',
            'email',
            'phone',
            'country',
            'country_id',
            'contacts',
        ]


class StorageLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = StorageLocation
        fields = '__all__'


class TruckSerializer(serializers.ModelSerializer):
    class Meta:
        model = Truck
        fields = '__all__'


class ContractItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)

    class Meta:
        model = ContractItem
        fields = '__all__'


class ContractSerializer(serializers.ModelSerializer):
    items = ContractItemSerializer(many=True, read_only=True)

    class Meta:
        model = Contract
        fields = '__all__'

