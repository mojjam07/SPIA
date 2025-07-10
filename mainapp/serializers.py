from rest_framework import serializers
from .models import StockItem, SalesRecord

class StockItemSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = StockItem
        fields = ['id', 'user', 'item_name', 'size', 'price', 'quantity', 'image', 'image_url', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']

    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image and hasattr(obj.image, 'url'):
            return request.build_absolute_uri(obj.image.url) if request else obj.image.url
        return '/static/images/stockpilot.png'

class SalesRecordSerializer(serializers.ModelSerializer):
    total = serializers.FloatField()

    class Meta:
        model = SalesRecord
        fields = ['id', 'user', 'items', 'total', 'timestamp', 'customer_name']
        read_only_fields = ['id', 'timestamp', 'user']
