from datetime import date

from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import (
    Coupon,
    PriceCategoryLimit,
    PriceCommand,
    PriceCommandItem,
    PriceList,
    PriceRestriction,
    StopListEntry,
)
from .serializers import (
    CouponSerializer,
    PriceCategoryLimitSerializer,
    PriceCommandItemSerializer,
    PriceCommandSerializer,
    PriceListSerializer,
    PriceRestrictionSerializer,
    StopListEntrySerializer,
)
from .services import DailyPriceCommandService


class PriceRestrictionViewSet(viewsets.ModelViewSet):
    queryset = PriceRestriction.objects.select_related('product')
    serializer_class = PriceRestrictionSerializer


class PriceListViewSet(viewsets.ModelViewSet):
    queryset = PriceList.objects.select_related('product', 'stock_area')
    serializer_class = PriceListSerializer
    filterset_fields = ['price_type', 'product', 'trading_point']


class PriceCategoryLimitViewSet(viewsets.ModelViewSet):
    queryset = PriceCategoryLimit.objects.all()
    serializer_class = PriceCategoryLimitSerializer


class CouponViewSet(viewsets.ModelViewSet):
    queryset = Coupon.objects.select_related('product_batch__product')
    serializer_class = CouponSerializer


class PriceCommandViewSet(viewsets.ModelViewSet):
    queryset = PriceCommand.objects.prefetch_related('items')
    serializer_class = PriceCommandSerializer
    filterset_fields = ['status', 'scheduled_for']

    @action(detail=False, methods=['post'])
    def run_daily(self, request):
        trading_point = request.data.get('trading_point', 'МХ-001')
        scheduled_for = request.data.get('scheduled_for')
        if scheduled_for:
            scheduled_for = date.fromisoformat(scheduled_for)
        else:
            scheduled_for = date.today()
        employee = getattr(request.user, 'employee', None)
        service = DailyPriceCommandService(
            trading_point=trading_point,
            scheduled_for=scheduled_for,
            actor=employee,
        )
        command = service.run()
        serializer = self.get_serializer(command)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def print_labels(self, request, pk=None):
        command = self.get_object()
        command.printed_at = timezone.now()
        command.save(update_fields=['printed_at', 'updated_at'])
        return Response(self.get_serializer(command).data)


class PriceCommandItemViewSet(viewsets.ModelViewSet):
    queryset = PriceCommandItem.objects.select_related('command', 'price')
    serializer_class = PriceCommandItemSerializer


class StopListEntryViewSet(viewsets.ModelViewSet):
    queryset = StopListEntry.objects.select_related('product')
    serializer_class = StopListEntrySerializer
