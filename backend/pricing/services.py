from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Dict, Iterable, List, Optional

from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from inventory.models import Product
from staff.models import Employee

from .models import (
    Coupon,
    PriceCategoryLimit,
    PriceCommand,
    PriceCommandItem,
    PriceList,
    PriceRestriction,
    StopListEntry,
)


@dataclass
class RestrictionConfig:
    max_markup_percent: Decimal
    max_daily_change_percent: Decimal
    allow_auto_markdown: bool
    markup_cap_percent: Decimal


class PriceRestrictionEvaluator:
    DEFAULT_MARKUP = Decimal('1000')
    DEFAULT_DAILY_CHANGE = Decimal('90')

    def __init__(self, product: Product, trading_point: str):
        self.product = product
        self.trading_point = trading_point

    def get_config(self) -> RestrictionConfig:
        product_restriction = getattr(self.product, 'price_restriction', None)
        if product_restriction:
            return RestrictionConfig(
                max_markup_percent=product_restriction.max_markup_percent,
                max_daily_change_percent=product_restriction.max_daily_change_percent,
                allow_auto_markdown=product_restriction.allow_auto_markdown,
                markup_cap_percent=product_restriction.max_markup_percent,
            )

        category_limit = None
        if self.product.category:
            category_limit = PriceCategoryLimit.objects.filter(category_name=self.product.category).first()

        if category_limit:
            return RestrictionConfig(
                max_markup_percent=category_limit.max_markup_percent,
                max_daily_change_percent=category_limit.max_daily_change_percent,
                allow_auto_markdown=True,
                markup_cap_percent=category_limit.markup_cap_percent,
            )

        return RestrictionConfig(
            max_markup_percent=self.DEFAULT_MARKUP,
            max_daily_change_percent=self.DEFAULT_DAILY_CHANGE,
            allow_auto_markdown=True,
            markup_cap_percent=self.DEFAULT_MARKUP,
        )

    def validate_candidate(self, candidate: PriceList, scheduled_for: date) -> Optional[str]:
        config = self.get_config()
        if candidate.input_price <= 0:
            return 'Входная цена должна быть > 0'
        markup = ((candidate.final_price - candidate.input_price) / candidate.input_price) * Decimal('100')
        if markup > config.max_markup_percent or markup > config.markup_cap_percent:
            return 'Превышено ограничение по наценке'

        last_price = (
            PriceList.objects.filter(
                product=candidate.product,
                trading_point=candidate.trading_point,
                valid_from__lt=scheduled_for,
                is_active=True,
            )
            .order_by('-valid_from')
            .first()
        )
        if last_price and last_price.final_price > 0:
            delta = abs((candidate.final_price - last_price.final_price) / last_price.final_price) * Decimal('100')
            if (
                delta > config.max_daily_change_percent
                and not (candidate.price_type == PriceList.MARKDOWN and config.allow_auto_markdown)
            ):
                return 'Превышено ограничение по суточному изменению'

        return None


class DailyPriceCommandService:
    """
    Picks minimal acceptable prices for every продукт магазина и формирует приказ.
    """

    def __init__(
        self,
        trading_point: str,
        scheduled_for: date,
        actor: Optional[Employee] = None,
    ):
        self.trading_point = trading_point
        self.scheduled_for = scheduled_for
        self.actor = actor

    @transaction.atomic
    def run(self) -> PriceCommand:
        command, created = PriceCommand.objects.get_or_create(
            trading_point=self.trading_point,
            scheduled_for=self.scheduled_for,
            defaults={
                'code': self._generate_code(),
                'status': PriceCommand.DRAFT,
                'created_by': self.actor,
                'notes': 'Автоматический приказ на день',
            },
        )
        if not created:
            command.items.all().delete()

        candidates = self._load_candidates()
        selected_count = 0
        for product_id, product_prices in candidates.items():
            candidate = self._select_candidate(product_prices)
            if not candidate:
                self._push_stop_list(product_id, 'Нет подходящих прайс-листов')
                continue

            item = PriceCommandItem.objects.create(
                command=command,
                price=candidate,
                coupon=self._pick_coupon(candidate.product),
                label_type=candidate.label_type,
                comment=candidate.reason,
            )
            selected_count += 1
            candidate.is_active = True
            candidate.regular_price = candidate.regular_price or candidate.final_price
            candidate.save(update_fields=['is_active', 'regular_price', 'updated_at'])

        command.status = PriceCommand.EXECUTED if selected_count else PriceCommand.STOPPED
        command.executed_at = timezone.now()
        command.executed_by = self.actor
        command.save(update_fields=['status', 'executed_at', 'executed_by', 'updated_at'])
        return command

    def _load_candidates(self) -> Dict[int, List[PriceList]]:
        price_qs = (
            PriceList.objects.select_related('product')
            .filter(
                trading_point=self.trading_point,
                valid_from__lte=self.scheduled_for,
            )
            .filter(Q(valid_to__isnull=True) | Q(valid_to__gte=self.scheduled_for))
        )
        grouped: Dict[int, List[PriceList]] = defaultdict(list)
        for price in price_qs:
            grouped[price.product_id].append(price)
        return grouped

    def _select_candidate(self, prices: Iterable[PriceList]) -> Optional[PriceList]:
        for candidate in sorted(prices, key=lambda p: p.final_price):
            reason = PriceRestrictionEvaluator(candidate.product, candidate.trading_point).validate_candidate(
                candidate, self.scheduled_for
            )
            if reason:
                self._push_stop_list(candidate.product_id, reason, candidate.final_price)
                continue
            return candidate
        return None

    def _pick_coupon(self, product: Product) -> Optional[Coupon]:
        coupon = (
            Coupon.objects.select_related('product_batch')
            .filter(
                product_batch__product=product,
                expires_at__gte=self.scheduled_for,
            )
            .order_by('expires_at')
            .first()
        )
        return coupon

    def _push_stop_list(self, product_id: int, reason: str, price: Optional[Decimal] = None):
        StopListEntry.objects.update_or_create(
            product_id=product_id,
            trading_point=self.trading_point,
            defaults={
                'reason': reason,
                'blocked_price': price or Decimal('0'),
            },
        )

    def _generate_code(self) -> str:
        return f'CMD-{self.trading_point}-{self.scheduled_for.strftime("%Y%m%d")}'


