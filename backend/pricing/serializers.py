from rest_framework import serializers

from .models import Coupon, PriceCommand, PriceCommandItem, PriceList, PriceRestriction, StopListEntry


class PriceRestrictionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PriceRestriction
        fields = '__all__'


class PriceListSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)

    class Meta:
        model = PriceList
        fields = '__all__'


class CouponSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coupon
        fields = '__all__'


class PriceCommandItemSerializer(serializers.ModelSerializer):
    price = PriceListSerializer(read_only=True)
    price_id = serializers.PrimaryKeyRelatedField(
        queryset=PriceList.objects.all(), write_only=True, source='price'
    )

    class Meta:
        model = PriceCommandItem
        fields = ['id', 'command', 'price', 'price_id', 'coupon', 'label_type', 'comment']


class PriceCommandSerializer(serializers.ModelSerializer):
    items = PriceCommandItemSerializer(many=True, read_only=True)

    class Meta:
        model = PriceCommand
        fields = '__all__'


class StopListEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = StopListEntry
        fields = '__all__'

