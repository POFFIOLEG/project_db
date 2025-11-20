from django.contrib import admin

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


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'sku', 'barcode', 'unit', 'shelf_life_days')
    search_fields = ('name', 'sku', 'barcode')


@admin.register(StockArea)
class StockAreaAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'area_type', 'parent_location')


@admin.register(Shelf)
class ShelfAdmin(admin.ModelAdmin):
    list_display = ('name', 'stock_area', 'code', 'max_items')


@admin.register(ProductBatch)
class ProductBatchAdmin(admin.ModelAdmin):
    list_display = ('batch_code', 'product', 'production_date', 'expiration_date', 'quantity')


@admin.register(StockItem)
class StockItemAdmin(admin.ModelAdmin):
    list_display = ('product', 'stock_area', 'quantity', 'expiration_date')


@admin.register(StockOperation)
class StockOperationAdmin(admin.ModelAdmin):
    list_display = ('product', 'operation_type', 'quantity', 'performed_at')
    list_filter = ('operation_type',)


@admin.register(WriteOffAct)
class WriteOffActAdmin(admin.ModelAdmin):
    list_display = ('product', 'reason', 'quantity', 'approved_at')


class InventoryLineInline(admin.TabularInline):
    model = InventoryLine
    extra = 0


@admin.register(InventorySession)
class InventorySessionAdmin(admin.ModelAdmin):
    list_display = ('code', 'scheduled_date', 'status')
    inlines = [InventoryLineInline]


class ReceivingItemInline(admin.TabularInline):
    model = ReceivingItem
    extra = 0


@admin.register(ReceivingOrder)
class ReceivingOrderAdmin(admin.ModelAdmin):
    list_display = ('code', 'supplier', 'expected_arrival', 'status')
    list_filter = ('status', 'supplier')
    search_fields = ('code',)
    inlines = [ReceivingItemInline]


@admin.register(ReceivingDiscrepancy)
class ReceivingDiscrepancyAdmin(admin.ModelAdmin):
    list_display = ('item', 'discrepancy_type', 'decision', 'reported_to_hq')
    list_filter = ('discrepancy_type', 'decision', 'reported_to_hq')


@admin.register(StockPlacement)
class StockPlacementAdmin(admin.ModelAdmin):
    list_display = ('stock_item', 'shelf', 'quantity')
