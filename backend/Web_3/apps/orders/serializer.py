# apps/orders/serializers.py
from rest_framework import serializers
from apps.orders.models import Order, OrderItem
from apps.companies.models import Company
from apps.products.models import Product

class OrderItemSerializer(serializers.ModelSerializer):
    subtotal = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)

    class Meta:
        model = OrderItem
        fields = ['order_item_id', 'product', 'quantity', 'unit_price', 'subtotal']

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("Quantity must be a positive integer greater than zero.")
        return value


class OrderDetailSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    buyer_company_name = serializers.ReadOnlyField(source='buyer_company.company_name')
    seller_company_name = serializers.ReadOnlyField(source='seller_company.company_name')

    class Meta:
        model = Order
        fields = [
            'order_id', 'buyer_company', 'buyer_company_name', 'seller_company', 
            'seller_company_name', 'order_number', 'total_amount', 
            'order_status', 'order_date', 'expected_delivery', 'items'
        ]


class OrderCreateSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, write_only=True)

    class Meta:
        model = Order
        fields = [
            'order_id', 'buyer_company', 'seller_company', 
            'order_number', 'order_status', 'order_date', 
            'expected_delivery', 'items'
        ]
        read_only_fields = ['order_status', 'order_date']

    def validate(self, data):
        if data['buyer_company'] == data['seller_company']:
            raise serializers.ValidationError({"seller_company": "The buyer company and seller company cannot be the same enterprise entity."})
        return data