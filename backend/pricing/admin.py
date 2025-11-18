from django.contrib import admin

from .models import Coupon, PriceCommand, PriceCommandItem, PriceList, PriceRestriction, StopListEntry


@admin.register(PriceRestriction)
class PriceRestrictionAdmin(admin.ModelAdmin):
    list_display = ('product', 'max_markup_percent', 'max_daily_change_percent', 'allow_auto_markdown')


@admin.register(PriceList)
class PriceListAdmin(admin.ModelAdmin):
    list_display = ('product', 'price_type', 'final_price', 'valid_from', 'is_active')
    list_filter = ('price_type', 'is_active')


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ('code', 'product_batch', 'discount_percent', 'expires_at')


class PriceCommandItemInline(admin.TabularInline):
    model = PriceCommandItem
    extra = 0


@admin.register(PriceCommand)
class PriceCommandAdmin(admin.ModelAdmin):
    list_display = ('code', 'scheduled_for', 'status', 'executed_at')
    inlines = [PriceCommandItemInline]


@admin.register(StopListEntry)
class StopListEntryAdmin(admin.ModelAdmin):
    list_display = ('product', 'trading_point', 'blocked_price', 'created_at')
