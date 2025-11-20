from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class PriceRestriction(models.Model):
    product = models.OneToOneField('inventory.Product', on_delete=models.CASCADE, related_name='price_restriction')
    max_markup_percent = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('1000'))
    max_daily_change_percent = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('90'))
    allow_auto_markdown = models.BooleanField(default=True)

    def __str__(self) -> str:
        return f'Ограничения для {self.product.name}'


class PriceCategoryLimit(models.Model):
    category_name = models.CharField(max_length=128, unique=True)
    max_markup_percent = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('1000'))
    max_daily_change_percent = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('90'))
    markup_cap_percent = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=Decimal('1000'),
        help_text='Максимальная наценка относительно входной цены (например 15 для 15%).',
    )

    def __str__(self) -> str:
        return f'Лимиты категории {self.category_name}'


class PriceList(models.Model):
    REGULAR = 'regular'
    MARKDOWN = 'markdown'
    PROMO = 'promo'
    TYPES = [
        (REGULAR, 'Регулярная'),
        (MARKDOWN, 'Уценка'),
        (PROMO, 'Акция'),
    ]

    LABEL_WHITE = 'white'
    LABEL_YELLOW = 'yellow'
    LABEL_PROMO = 'promo'
    SOURCE_HQ = 'hq'
    SOURCE_SUPPLIER = 'supplier'
    SOURCE_ANALYTICS = 'analytics'
    SOURCE_LOCAL = 'local'
    SOURCES = [
        (SOURCE_HQ, 'ГК'),
        (SOURCE_SUPPLIER, 'Поставщик'),
        (SOURCE_ANALYTICS, 'Аналитика'),
        (SOURCE_LOCAL, 'МХ'),
    ]

    trading_point = models.CharField(max_length=128, default='МХ-001')
    product = models.ForeignKey('inventory.Product', on_delete=models.CASCADE, related_name='prices')
    stock_area = models.ForeignKey('inventory.StockArea', on_delete=models.SET_NULL, null=True, blank=True)
    price_type = models.CharField(max_length=16, choices=TYPES, default=REGULAR)
    input_price = models.DecimalField(max_digits=12, decimal_places=2)
    final_price = models.DecimalField(max_digits=12, decimal_places=2)
    regular_price = models.DecimalField(max_digits=12, decimal_places=2)
    label_type = models.CharField(
        max_length=16,
        choices=[
            (LABEL_WHITE, 'Белый'),
            (LABEL_YELLOW, 'Жёлтый'),
            (LABEL_PROMO, 'Акционный'),
        ],
        default=LABEL_WHITE,
    )
    source = models.CharField(max_length=16, choices=SOURCES, default=SOURCE_HQ)
    valid_from = models.DateField()
    valid_to = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    reason = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['-valid_from']

    def __str__(self) -> str:
        return f'{self.product.name} - {self.final_price} ₽'

    def clean(self):
        if self.final_price <= 0:
            raise ValidationError('Финальная цена должна быть больше нуля')
        if self.input_price <= 0:
            raise ValidationError('Входная цена должна быть больше нуля')

        restriction = getattr(self.product, 'price_restriction', None)
        if restriction:
            markup = ((self.final_price - self.input_price) / self.input_price) * 100
            if markup > restriction.max_markup_percent:
                raise ValidationError('Превышено ограничение по наценке')

            last_price = (
                PriceList.objects.filter(product=self.product, trading_point=self.trading_point)
                .exclude(pk=self.pk)
                .order_by('-valid_from')
                .first()
            )
            if last_price and restriction.max_daily_change_percent:
                base_price = last_price.final_price
                if base_price > 0:
                    delta = abs((self.final_price - base_price) / base_price) * 100
                    if (
                        delta > restriction.max_daily_change_percent
                        and not (self.price_type == self.MARKDOWN and restriction.allow_auto_markdown)
                    ):
                        raise ValidationError('Превышено ограничение по изменению цены за день')

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class Coupon(models.Model):
    product_batch = models.ForeignKey('inventory.ProductBatch', on_delete=models.CASCADE, related_name='coupons')
    code = models.CharField(max_length=64, unique=True)
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2)
    expires_at = models.DateField()
    note = models.CharField(max_length=255, blank=True)

    def __str__(self) -> str:
        return self.code


class PriceCommand(models.Model):
    DRAFT = 'draft'
    EXECUTED = 'executed'
    STOPPED = 'stopped'
    STATUSES = [
        (DRAFT, 'Черновик'),
        (EXECUTED, 'Выполнен'),
        (STOPPED, 'Стоп-лист'),
    ]

    code = models.CharField(max_length=32, unique=True)
    scheduled_for = models.DateField()
    status = models.CharField(max_length=16, choices=STATUSES, default=DRAFT)
    created_by = models.ForeignKey('staff.Employee', on_delete=models.SET_NULL, null=True, related_name='price_orders')
    executed_at = models.DateTimeField(null=True, blank=True)
    executed_by = models.ForeignKey(
        'staff.Employee',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='executed_price_orders',
    )
    trading_point = models.CharField(max_length=128, default='МХ-001')
    printed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    def __str__(self) -> str:
        return self.code


class PriceCommandItem(models.Model):
    command = models.ForeignKey(PriceCommand, on_delete=models.CASCADE, related_name='items')
    price = models.ForeignKey(PriceList, on_delete=models.CASCADE, related_name='command_items')
    coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True, blank=True)
    label_type = models.CharField(max_length=16, default=PriceList.LABEL_WHITE)
    comment = models.CharField(max_length=255, blank=True)

    class Meta:
        unique_together = ('command', 'price')


class StopListEntry(models.Model):
    product = models.ForeignKey('inventory.Product', on_delete=models.CASCADE)
    trading_point = models.CharField(max_length=128)
    reason = models.TextField()
    blocked_price = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('product', 'trading_point')
