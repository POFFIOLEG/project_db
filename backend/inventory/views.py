from rest_framework import viewsets

from .models import (
    InventoryLine,
    InventorySession,
    Product,
    ProductBatch,
    Shelf,
    StockArea,
    StockItem,
    StockOperation,
    WriteOffAct,
)
from .serializers import (
    InventoryLineSerializer,
    InventorySessionSerializer,
    ProductBatchSerializer,
    ProductSerializer,
    ShelfSerializer,
    StockAreaSerializer,
    StockItemSerializer,
    StockOperationSerializer,
    WriteOffActSerializer,
)


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


class StockItemViewSet(viewsets.ModelViewSet):
    queryset = StockItem.objects.select_related('product', 'stock_area').all()
    serializer_class = StockItemSerializer
    filterset_fields = ['stock_area', 'product']


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
