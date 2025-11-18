from django.conf import settings
from django.db import models


class TimestampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Product(TimestampedModel):
    UNIT_CHOICES = [
        ('pcs', 'шт.'),
        ('kg', 'кг'),
        ('l', 'л'),
        ('pack', 'уп.'),
    ]

    name = models.CharField(max_length=255)
    sku = models.CharField(max_length=64, unique=True)
    manufacturer = models.ForeignKey('references.Manufacturer', on_delete=models.PROTECT, related_name='products')
    manufacturer_code = models.CharField(max_length=64, blank=True)
    country = models.ForeignKey('references.Country', on_delete=models.PROTECT, related_name='products')
    dimensions = models.CharField(max_length=128, blank=True)
    unit = models.CharField(max_length=16, choices=UNIT_CHOICES, default='pcs')
    shelf_life_days = models.PositiveIntegerField(default=0)
    barcode = models.CharField(max_length=32, unique=True)
    category = models.CharField(max_length=128, blank=True)
    extra_info = models.TextField(blank=True)

    def __str__(self) -> str:
        return self.name


class StockArea(TimestampedModel):
    WAREHOUSE = 'warehouse'
    SALES = 'sales'
    COLD = 'cold'
    TYPES = [
        (WAREHOUSE, 'Склад'),
        (SALES, 'Торговый зал'),
        (COLD, 'Холодильник'),
    ]

    code = models.CharField(max_length=32, unique=True)
    name = models.CharField(max_length=255)
    area_type = models.CharField(max_length=32, choices=TYPES, default=WAREHOUSE)
    parent_location = models.ForeignKey('references.StorageLocation', on_delete=models.CASCADE, related_name='areas')
    max_capacity = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    temperature_min = models.FloatField(null=True, blank=True)
    temperature_max = models.FloatField(null=True, blank=True)

    def __str__(self) -> str:
        return self.name


class Shelf(TimestampedModel):
    stock_area = models.ForeignKey(StockArea, on_delete=models.CASCADE, related_name='shelves')
    code = models.CharField(max_length=32)
    name = models.CharField(max_length=128)
    max_items = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('stock_area', 'code')

    def __str__(self) -> str:
        return f'{self.stock_area.name} - {self.code}'


class ProductBatch(TimestampedModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='batches')
    batch_code = models.CharField(max_length=64, unique=True)
    contract_item = models.ForeignKey('references.ContractItem', on_delete=models.SET_NULL, null=True, blank=True)
    production_date = models.DateField()
    expiration_date = models.DateField()
    quantity = models.DecimalField(max_digits=12, decimal_places=3)
    input_price = models.DecimalField(max_digits=12, decimal_places=2)
    delivery_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=32, default='pending')

    def __str__(self) -> str:
        return f'{self.product.name} ({self.batch_code})'


class StockItem(TimestampedModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='stock_items')
    batch = models.ForeignKey(ProductBatch, on_delete=models.CASCADE, related_name='stock_items')
    stock_area = models.ForeignKey(StockArea, on_delete=models.CASCADE, related_name='stock_items')
    quantity = models.DecimalField(max_digits=12, decimal_places=3)
    reserved_quantity = models.DecimalField(max_digits=12, decimal_places=3, default=0)
    expiration_date = models.DateField()

    class Meta:
        unique_together = ('batch', 'stock_area')


class StockOperation(TimestampedModel):
    RECEIPT = 'receipt'
    MOVE = 'move'
    ISSUE = 'issue'
    WRITE_OFF = 'write_off'
    SALE = 'sale'
    TYPES = [
        (RECEIPT, 'Приход'),
        (MOVE, 'Перемещение'),
        (ISSUE, 'Расход'),
        (WRITE_OFF, 'Списание'),
        (SALE, 'Продажа'),
    ]

    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    batch = models.ForeignKey(ProductBatch, on_delete=models.PROTECT)
    source_area = models.ForeignKey(
        StockArea, on_delete=models.SET_NULL, null=True, blank=True, related_name='source_operations'
    )
    target_area = models.ForeignKey(
        StockArea, on_delete=models.SET_NULL, null=True, blank=True, related_name='target_operations'
    )
    quantity = models.DecimalField(max_digits=12, decimal_places=3)
    operation_type = models.CharField(max_length=16, choices=TYPES)
    performed_by = models.ForeignKey('staff.Employee', on_delete=models.SET_NULL, null=True, blank=True)
    performed_at = models.DateTimeField(auto_now_add=True)
    note = models.TextField(blank=True)


class WriteOffAct(TimestampedModel):
    FORCE_MAJEURE = 'force_majeure'
    EXPIRED = 'expired'
    THEFT = 'theft'
    NEGLIGENCE = 'negligence'
    OTHER = 'other'
    REASONS = [
        (FORCE_MAJEURE, 'Форс-мажор'),
        (EXPIRED, 'Истёк срок годности'),
        (THEFT, 'Кража'),
        (NEGLIGENCE, 'Халатность'),
        (OTHER, 'Другое'),
    ]

    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    batch = models.ForeignKey(ProductBatch, on_delete=models.PROTECT)
    quantity = models.DecimalField(max_digits=12, decimal_places=3)
    reason = models.CharField(max_length=32, choices=REASONS)
    comment = models.TextField(blank=True)
    created_by = models.ForeignKey('staff.Employee', on_delete=models.SET_NULL, null=True, related_name='write_offs')
    approved_by = models.ForeignKey(
        'staff.Employee',
        on_delete=models.SET_NULL,
        null=True,
        related_name='approved_write_offs',
    )
    approved_at = models.DateTimeField(null=True, blank=True)


class InventorySession(TimestampedModel):
    OPEN = 'open'
    APPROVAL = 'approval'
    CLOSED = 'closed'
    STATUSES = [
        (OPEN, 'В процессе'),
        (APPROVAL, 'Ожидает подтверждения'),
        (CLOSED, 'Закрыта'),
    ]

    code = models.CharField(max_length=32, unique=True)
    scheduled_date = models.DateField()
    status = models.CharField(max_length=16, choices=STATUSES, default=OPEN)
    created_by = models.ForeignKey('staff.Employee', on_delete=models.SET_NULL, null=True, related_name='inventory_runs')
    approved_by = models.ForeignKey(
        'staff.Employee',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='inventory_approvals',
    )
    notes = models.TextField(blank=True)

    def __str__(self) -> str:
        return self.code


class InventoryLine(TimestampedModel):
    session = models.ForeignKey(InventorySession, on_delete=models.CASCADE, related_name='lines')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    stock_area = models.ForeignKey(StockArea, on_delete=models.PROTECT)
    system_qty = models.DecimalField(max_digits=12, decimal_places=3)
    actual_qty = models.DecimalField(max_digits=12, decimal_places=3)
    comment = models.TextField(blank=True)

    @property
    def difference(self):
        return self.actual_qty - self.system_qty
