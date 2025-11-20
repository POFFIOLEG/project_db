from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Iterable, Optional

from django.db import transaction
from django.utils import timezone

from .models import (
    ProductBatch,
    ReceivingDiscrepancy,
    ReceivingItem,
    ReceivingOrder,
    Shelf,
    StockArea,
    StockItem,
    StockOperation,
    StockPlacement,
)


class ReceivingWorkflowService:
    """
    Handles the end-to-end flow of receiving orders: start, discrepancy handling, completion.
    """

    def __init__(self, order: ReceivingOrder, actor=None):
        self.order = order
        self.actor = actor

    @transaction.atomic
    def start(self) -> ReceivingOrder:
        if self.order.status != ReceivingOrder.PLANNED:
            return self.order
        self.order.status = ReceivingOrder.IN_PROGRESS
        self.order.actual_arrival = timezone.now()
        if self.actor and not self.order.received_by:
            self.order.received_by = getattr(self.actor, "employee", None)
        self.order.save(update_fields=['status', 'actual_arrival', 'received_by', 'updated_at'])
        return self.order

    @transaction.atomic
    def complete(self) -> ReceivingOrder:
        if self.order.status not in (ReceivingOrder.IN_PROGRESS, ReceivingOrder.PLANNED):
            return self.order

        pending_items = self.order.items.filter(status__in=[ReceivingItem.PENDING, ReceivingItem.WAITING_HQ])
        if pending_items.exists():
            raise ValueError('Не все позиции обработаны или получено решение ГК.')

        for item in self.order.items.all():
            if item.status != ReceivingItem.ACCEPTED:
                continue
            if not item.stock_area:
                raise ValueError(f'Не указано место хранения для {item.product}')
            if not item.received_quantity or item.received_quantity <= 0:
                raise ValueError(f'Не указано фактическое количество для {item.product}')
            if not item.production_date or not item.expiration_date:
                raise ValueError(f'Не указаны даты производства/годности для {item.product}')

            batch = self._create_batch(item)
            self._increment_stock(item, batch)
            item.batch = batch
            item.save(update_fields=['batch', 'updated_at'])

        self.order.status = ReceivingOrder.COMPLETED
        self.order.save(update_fields=['status', 'updated_at'])
        return self.order

    def _create_batch(self, item: ReceivingItem) -> ProductBatch:
        batch_code = item.batch_code_hint or f'{self.order.code}-{uuid.uuid4().hex[:8]}'
        batch, created = ProductBatch.objects.get_or_create(
            batch_code=batch_code,
            defaults={
                'product': item.product,
                'contract_item': item.contract_item,
                'production_date': item.production_date,
                'expiration_date': item.expiration_date,
                'quantity': item.received_quantity,
                'input_price': item.input_price or Decimal('0'),
                'delivery_price': item.delivery_price or Decimal('0'),
                'status': 'stored',
            },
        )
        if not created:
            batch.quantity = item.received_quantity
            batch.production_date = item.production_date
            batch.expiration_date = item.expiration_date
            batch.input_price = item.input_price or batch.input_price
            batch.delivery_price = item.delivery_price or batch.delivery_price
            batch.save()
        return batch

    def _increment_stock(self, item: ReceivingItem, batch: ProductBatch) -> None:
        stock_item, created = StockItem.objects.get_or_create(
            batch=batch,
            stock_area=item.stock_area,
            defaults={
                'product': item.product,
                'quantity': item.received_quantity,
                'reserved_quantity': 0,
                'expiration_date': item.expiration_date,
            },
        )
        if not created:
            stock_item.quantity += item.received_quantity
            stock_item.expiration_date = item.expiration_date
            stock_item.save()

        StockOperation.objects.create(
            product=item.product,
            batch=batch,
            source_area=None,
            target_area=item.stock_area,
            quantity=item.received_quantity,
            operation_type=StockOperation.RECEIPT,
            performed_by=getattr(self.actor, "employee", None),
            note=f'Приёмка {self.order.code}',
        )


class StockMovementService:
    """
    Helper for moving goods between warehouse areas or distributing to shelves.
    """

    def __init__(self, performer=None):
        self.performer = performer

    @transaction.atomic
    def move(
        self,
        batch: ProductBatch,
        source_area: StockArea,
        target_area: StockArea,
        quantity: Decimal,
        note: str = '',
    ) -> StockOperation:
        if quantity <= 0:
            raise ValueError('Количество должно быть положительным.')

        source_item = StockItem.objects.get(batch=batch, stock_area=source_area)
        if source_item.quantity < quantity:
            raise ValueError('Недостаточно остатка для перемещения.')
        source_item.quantity -= quantity
        source_item.save()

        target_item, created = StockItem.objects.get_or_create(
            batch=batch,
            stock_area=target_area,
            defaults={
                'product': batch.product,
                'quantity': quantity,
                'reserved_quantity': 0,
                'expiration_date': batch.expiration_date,
            },
        )
        if not created:
            target_item.quantity += quantity
            target_item.save()

        return StockOperation.objects.create(
            product=batch.product,
            batch=batch,
            source_area=source_area,
            target_area=target_area,
            quantity=quantity,
            operation_type=StockOperation.MOVE,
            performed_by=getattr(self.performer, "employee", None),
            note=note or 'Перемещение между зонами',
        )

    @transaction.atomic
    def place_on_shelves(
        self,
        stock_item: StockItem,
        placements: Iterable[dict],
    ) -> None:
        """
        placements: [{'shelf_id': 1, 'quantity': '5.0', 'note': ''}, ...]
        """
        total = Decimal('0')
        for placement in placements:
            quantity = Decimal(str(placement['quantity']))
            if quantity <= 0:
                raise ValueError('Количество должно быть положительным.')
            total += quantity

        if total > stock_item.quantity:
            raise ValueError('Нельзя разложить больше, чем доступно на складе.')

        for placement in placements:
            shelf = Shelf.objects.get(pk=placement['shelf_id'])
            quantity = Decimal(str(placement['quantity']))
            StockPlacement.objects.update_or_create(
                stock_item=stock_item,
                shelf=shelf,
                defaults={
                    'quantity': quantity,
                    'note': placement.get('note', ''),
                },
            )


