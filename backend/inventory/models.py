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


class ReceivingOrder(TimestampedModel):
    PLANNED = 'planned'
    IN_PROGRESS = 'in_progress'
    COMPLETED = 'completed'
    CANCELLED = 'cancelled'
    STATUSES = [
        (PLANNED, 'Запланирована'),
        (IN_PROGRESS, 'В работе'),
        (COMPLETED, 'Завершена'),
        (CANCELLED, 'Отменена'),
    ]

    code = models.CharField(max_length=32, unique=True)
    contract = models.ForeignKey('references.Contract', on_delete=models.SET_NULL, null=True, blank=True)
    supplier = models.ForeignKey('references.Supplier', on_delete=models.SET_NULL, null=True, blank=True)
    storage_location = models.ForeignKey(
        'references.StorageLocation', on_delete=models.SET_NULL, null=True, blank=True
    )
    expected_arrival = models.DateField()
    actual_arrival = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=16, choices=STATUSES, default=PLANNED)
    created_by = models.ForeignKey(
        'staff.Employee',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_receivings',
    )
    received_by = models.ForeignKey(
        'staff.Employee',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='processed_receivings',
    )
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-expected_arrival', '-created_at']

    def __str__(self) -> str:
        return self.code


class ReceivingItem(TimestampedModel):
    PENDING = 'pending'
    ACCEPTED = 'accepted'
    REJECTED = 'rejected'
    WAITING_HQ = 'waiting_hq'
    STATUSES = [
        (PENDING, 'Ожидает проверки'),
        (ACCEPTED, 'Принят'),
        (REJECTED, 'Отклонён'),
        (WAITING_HQ, 'Ожидает решения ГК'),
    ]

    order = models.ForeignKey(ReceivingOrder, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    contract_item = models.ForeignKey('references.ContractItem', on_delete=models.SET_NULL, null=True, blank=True)
    expected_quantity = models.DecimalField(max_digits=12, decimal_places=3)
    received_quantity = models.DecimalField(max_digits=12, decimal_places=3, null=True, blank=True)
    production_date = models.DateField(null=True, blank=True)
    expiration_date = models.DateField(null=True, blank=True)
    shelf_life_ok = models.BooleanField(default=True)
    stock_area = models.ForeignKey(StockArea, on_delete=models.SET_NULL, null=True, blank=True)
    batch_code_hint = models.CharField(max_length=64, blank=True)
    input_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    delivery_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    comment = models.TextField(blank=True)
    status = models.CharField(max_length=16, choices=STATUSES, default=PENDING)
    batch = models.OneToOneField(
        ProductBatch,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='receiving_link',
    )

    def __str__(self) -> str:
        return f'{self.order.code} - {self.product.name}'


class ReceivingDiscrepancy(TimestampedModel):
    TYPE_QUANTITY = 'quantity'
    TYPE_QUALITY = 'quality'
    TYPE_EXPIRATION = 'expiration'
    TYPE_DAMAGE = 'damage'
    TYPE_OTHER = 'other'
    TYPES = [
        (TYPE_QUANTITY, 'Количество'),
        (TYPE_QUALITY, 'Качество/ассортимент'),
        (TYPE_EXPIRATION, 'Срок годности'),
        (TYPE_DAMAGE, 'Повреждение'),
        (TYPE_OTHER, 'Другое'),
    ]

    DECISION_PENDING = 'pending'
    DECISION_ACCEPT = 'accept'
    DECISION_REJECT = 'reject'
    DECISION_CHOICES = [
        (DECISION_PENDING, 'Ожидает решения'),
        (DECISION_ACCEPT, 'Принять товар'),
        (DECISION_REJECT, 'Отказать в приёмке'),
    ]

    item = models.ForeignKey(ReceivingItem, on_delete=models.CASCADE, related_name='discrepancies')
    discrepancy_type = models.CharField(max_length=32, choices=TYPES, default=TYPE_OTHER)
    description = models.TextField()
    reported_to_hq = models.BooleanField(default=False)
    hq_ticket = models.CharField(max_length=64, blank=True)
    decision = models.CharField(max_length=16, choices=DECISION_CHOICES, default=DECISION_PENDING)
    decided_by = models.ForeignKey(
        'staff.Employee',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='discrepancy_decisions',
    )
    decided_at = models.DateTimeField(null=True, blank=True)
    decision_comment = models.TextField(blank=True)

    def __str__(self) -> str:
        return f'Несоответствие {self.item_id} ({self.get_discrepancy_type_display()})'


class StockPlacement(TimestampedModel):
    stock_item = models.ForeignKey(StockItem, on_delete=models.CASCADE, related_name='placements')
    shelf = models.ForeignKey(Shelf, on_delete=models.CASCADE, related_name='placements')
    quantity = models.DecimalField(max_digits=12, decimal_places=3)
    note = models.CharField(max_length=255, blank=True)

    class Meta:
        unique_together = ('stock_item', 'shelf')
