from rest_framework import serializers

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


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'


class StockAreaSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockArea
        fields = '__all__'


class ShelfSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shelf
        fields = '__all__'


class ProductBatchSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)

    class Meta:
        model = ProductBatch
        fields = '__all__'


class StockItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(), write_only=True, source='product'
    )

    class Meta:
        model = StockItem
        fields = ['id', 'product', 'product_id', 'batch', 'stock_area', 'quantity', 'reserved_quantity', 'expiration_date']


class StockOperationSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockOperation
        fields = '__all__'


class WriteOffActSerializer(serializers.ModelSerializer):
    class Meta:
        model = WriteOffAct
        fields = '__all__'


class InventoryLineSerializer(serializers.ModelSerializer):
    difference = serializers.DecimalField(max_digits=12, decimal_places=3, read_only=True)

    class Meta:
        model = InventoryLine
        fields = '__all__'


class InventorySessionSerializer(serializers.ModelSerializer):
    lines = InventoryLineSerializer(many=True, read_only=True)

    class Meta:
        model = InventorySession
        fields = '__all__'

