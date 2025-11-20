from decimal import Decimal

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import (
    InventoryLine,
    InventorySession,
    Product,
    ProductBatch,
    ReceivingDiscrepancy,
    ReceivingItem,
    ReceivingOrder,
    Shelf,
    StockArea,
    StockItem,
    StockOperation,
    StockPlacement,
    WriteOffAct,
)
from .serializers import (
    InventoryLineSerializer,
    InventorySessionSerializer,
    ProductBatchSerializer,
    ProductSerializer,
    ReceivingDiscrepancySerializer,
    ReceivingItemSerializer,
    ReceivingOrderSerializer,
    ShelfSerializer,
    StockAreaSerializer,
    StockItemSerializer,
    StockOperationSerializer,
    StockPlacementSerializer,
    WriteOffActSerializer,
)
from .services import ReceivingWorkflowService, StockMovementService


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.select_related('manufacturer', 'country').all()
    serializer_class = ProductSerializer
    search_fields = ['name', 'barcode', 'sku']
    filterset_fields = ['category']


class StockAreaViewSet(viewsets.ModelViewSet):
    queryset = StockArea.objects.select_related('parent_location').all()
    serializer_class = StockAreaSerializer


class ShelfViewSet(viewsets.ModelViewSet):
    queryset = Shelf.objects.select_related('stock_area').all()
    serializer_class = ShelfSerializer


class ProductBatchViewSet(viewsets.ModelViewSet):
    queryset = ProductBatch.objects.select_related('product').all()
    serializer_class = ProductBatchSerializer
    filterset_fields = ['product', 'status']

    @action(detail=True, methods=['post'])
    def move(self, request, pk=None):
        batch = self.get_object()
        try:
            source_area = StockArea.objects.get(pk=request.data['source_area'])
            target_area = StockArea.objects.get(pk=request.data['target_area'])
            quantity = Decimal(str(request.data['quantity']))
        except (KeyError, StockArea.DoesNotExist, ValueError) as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        service = StockMovementService(performer=request.user)
        try:
            operation = service.move(
                batch=batch,
                source_area=source_area,
                target_area=target_area,
                quantity=quantity,
                note=request.data.get('note', ''),
            )
        except (ValueError, StockItem.DoesNotExist) as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(StockOperationSerializer(operation).data, status=status.HTTP_201_CREATED)


class StockItemViewSet(viewsets.ModelViewSet):
    queryset = StockItem.objects.select_related('product', 'stock_area').all()
    serializer_class = StockItemSerializer
    filterset_fields = ['stock_area', 'product']

    @action(detail=True, methods=['post'])
    def place(self, request, pk=None):
        stock_item = self.get_object()
        placements = request.data.get('placements', [])
        if not isinstance(placements, list) or not placements:
            return Response({'detail': 'Не переданы размещения.'}, status=status.HTTP_400_BAD_REQUEST)
        service = StockMovementService(performer=request.user)
        try:
            service.place_on_shelves(stock_item, placements)
        except (ValueError, Shelf.DoesNotExist) as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'status': 'ok'})


class StockOperationViewSet(viewsets.ModelViewSet):
    queryset = StockOperation.objects.select_related('product', 'batch').all()
    serializer_class = StockOperationSerializer
    filterset_fields = ['operation_type', 'product', 'performed_by']


class WriteOffActViewSet(viewsets.ModelViewSet):
    queryset = WriteOffAct.objects.select_related('product', 'batch').all()
    serializer_class = WriteOffActSerializer


class InventorySessionViewSet(viewsets.ModelViewSet):
    queryset = InventorySession.objects.prefetch_related('lines').all()
    serializer_class = InventorySessionSerializer
    filterset_fields = ['status']


class InventoryLineViewSet(viewsets.ModelViewSet):
    queryset = InventoryLine.objects.select_related('session', 'product', 'stock_area').all()
    serializer_class = InventoryLineSerializer


class ReceivingOrderViewSet(viewsets.ModelViewSet):
    queryset = ReceivingOrder.objects.prefetch_related('items__product').select_related(
        'supplier', 'contract', 'storage_location'
    )
    serializer_class = ReceivingOrderSerializer
    filterset_fields = ['status', 'supplier', 'expected_arrival']

    def perform_create(self, serializer):
        employee = getattr(self.request.user, 'employee', None)
        serializer.save(created_by=employee)

    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        order = self.get_object()
        ReceivingWorkflowService(order, actor=request.user).start()
        return Response(self.get_serializer(order).data)

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        order = self.get_object()
        service = ReceivingWorkflowService(order, actor=request.user)
        try:
            service.complete()
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(self.get_serializer(order).data)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        order = self.get_object()
        order.status = ReceivingOrder.CANCELLED
        order.save(update_fields=['status', 'updated_at'])
        return Response(self.get_serializer(order).data)


class ReceivingItemViewSet(viewsets.ModelViewSet):
    queryset = ReceivingItem.objects.select_related('order', 'product', 'stock_area').all()
    serializer_class = ReceivingItemSerializer
    filterset_fields = ['order', 'status', 'product']

    @action(detail=True, methods=['post'])
    def set_status(self, request, pk=None):
        item = self.get_object()
        status_value = request.data.get('status')
        if status_value not in dict(ReceivingItem.STATUSES):
            return Response({'detail': 'Некорректный статус'}, status=status.HTTP_400_BAD_REQUEST)
        item.status = status_value
        item.save(update_fields=['status', 'updated_at'])
        return Response(self.get_serializer(item).data)


class ReceivingDiscrepancyViewSet(viewsets.ModelViewSet):
    queryset = ReceivingDiscrepancy.objects.select_related('item', 'item__order').all()
    serializer_class = ReceivingDiscrepancySerializer
    filterset_fields = ['item', 'decision', 'discrepancy_type']


class StockPlacementViewSet(viewsets.ModelViewSet):
    queryset = StockPlacement.objects.select_related('stock_item', 'shelf').all()
    serializer_class = StockPlacementSerializer
    filterset_fields = ['shelf', 'stock_item']
