from django.db import models


class TimestampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Country(TimestampedModel):
    code = models.CharField(max_length=3, unique=True)
    name = models.CharField(max_length=128)

    def __str__(self) -> str:
        return f'{self.name} ({self.code})'


class Manufacturer(TimestampedModel):
    name = models.CharField(max_length=255)
    country = models.ForeignKey(Country, on_delete=models.PROTECT, related_name='manufacturers')
    company_code = models.CharField(max_length=32, blank=True)

    def __str__(self) -> str:
        return self.name


class Supplier(TimestampedModel):
    name = models.CharField(max_length=255)
    tax_number = models.CharField(max_length=32, blank=True)
    country = models.ForeignKey(Country, on_delete=models.PROTECT, related_name='suppliers')
    address = models.TextField(blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=32, blank=True)

    def __str__(self) -> str:
        return self.name


class SupplierContact(TimestampedModel):
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='contacts')
    name = models.CharField(max_length=255)
    position = models.CharField(max_length=128, blank=True)
    phone = models.CharField(max_length=32, blank=True)
    email = models.EmailField(blank=True)

    def __str__(self) -> str:
        return f'{self.name} ({self.supplier.name})'


class StorageLocation(TimestampedModel):
    WAREHOUSE = 'warehouse'
    SHOP_FLOOR = 'shop_floor'
    DISTRIBUTION_CENTER = 'dc'
    HQ = 'hq'
    TYPES = [
        (WAREHOUSE, 'Склад'),
        (SHOP_FLOOR, 'Торговый зал'),
        (DISTRIBUTION_CENTER, 'Распределительный центр'),
        (HQ, 'Головной офис'),
    ]

    code = models.CharField(max_length=32, unique=True)
    name = models.CharField(max_length=255)
    location_type = models.CharField(max_length=32, choices=TYPES, default=WAREHOUSE)
    address = models.TextField(blank=True)
    temperature_min = models.FloatField(null=True, blank=True)
    temperature_max = models.FloatField(null=True, blank=True)
    capacity_units = models.PositiveIntegerField(default=0)

    def __str__(self) -> str:
        return self.name


class Truck(TimestampedModel):
    number = models.CharField(max_length=32, unique=True)
    capacity_kg = models.PositiveIntegerField()
    driver_name = models.CharField(max_length=255, blank=True)
    active = models.BooleanField(default=True)

    def __str__(self) -> str:
        return self.number


class Contract(TimestampedModel):
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, related_name='contracts')
    contract_number = models.CharField(max_length=64, unique=True)
    signed_at = models.DateField()
    valid_until = models.DateField(null=True, blank=True)
    direct_delivery = models.BooleanField(default=False)
    storage_location = models.ForeignKey(
        StorageLocation,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='contracts',
    )
    truck = models.ForeignKey(Truck, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self) -> str:
        return f'{self.contract_number} - {self.supplier.name}'


class ContractItem(TimestampedModel):
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('inventory.Product', on_delete=models.CASCADE, related_name='contract_items')
    expected_quantity = models.DecimalField(max_digits=12, decimal_places=3)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        unique_together = ('contract', 'product')

    def __str__(self) -> str:
        return f'{self.product.name} ({self.contract.contract_number})'
