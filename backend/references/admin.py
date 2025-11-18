from django.contrib import admin

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


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ('name', 'code')
    search_fields = ('name', 'code')


@admin.register(Manufacturer)
class ManufacturerAdmin(admin.ModelAdmin):
    list_display = ('name', 'country', 'company_code')
    search_fields = ('name',)


class SupplierContactInline(admin.TabularInline):
    model = SupplierContact
    extra = 1


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'country', 'phone', 'email')
    inlines = [SupplierContactInline]


@admin.register(StorageLocation)
class StorageLocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'location_type')
    list_filter = ('location_type',)


@admin.register(Truck)
class TruckAdmin(admin.ModelAdmin):
    list_display = ('number', 'capacity_kg', 'driver_name', 'active')


class ContractItemInline(admin.TabularInline):
    model = ContractItem
    extra = 1


@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = ('contract_number', 'supplier', 'signed_at', 'valid_until', 'direct_delivery')
    inlines = [ContractItemInline]
