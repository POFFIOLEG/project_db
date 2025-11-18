from rest_framework import viewsets

from .models import Coupon, PriceCommand, PriceCommandItem, PriceList, PriceRestriction, StopListEntry
from .serializers import (
    CouponSerializer,
    PriceCommandItemSerializer,
    PriceCommandSerializer,
    PriceListSerializer,
    PriceRestrictionSerializer,
    StopListEntrySerializer,
)


class PriceRestrictionViewSet(viewsets.ModelViewSet):
    queryset = PriceRestriction.objects.select_related('product')
    serializer_class = PriceRestrictionSerializer


class PriceListViewSet(viewsets.ModelViewSet):
    queryset = PriceList.objects.select_related('product', 'stock_area')
    serializer_class = PriceListSerializer
    filterset_fields = ['price_type', 'product', 'trading_point']


class CouponViewSet(viewsets.ModelViewSet):
    queryset = Coupon.objects.select_related('product_batch__product')
    serializer_class = CouponSerializer


class PriceCommandViewSet(viewsets.ModelViewSet):
    queryset = PriceCommand.objects.prefetch_related('items')
    serializer_class = PriceCommandSerializer
    filterset_fields = ['status', 'scheduled_for']


class PriceCommandItemViewSet(viewsets.ModelViewSet):
    queryset = PriceCommandItem.objects.select_related('command', 'price')
    serializer_class = PriceCommandItemSerializer


class StopListEntryViewSet(viewsets.ModelViewSet):
    queryset = StopListEntry.objects.select_related('product')
    serializer_class = StopListEntrySerializer
