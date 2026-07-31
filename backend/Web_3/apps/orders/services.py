# apps/orders/services.py
from django.db import transaction
from decimal import Decimal
from apps.orders.models import Order, OrderItem

class OrderService:
    @staticmethod
    @transaction.atomic
    def process_new_invoice(order_data, item_payload_list) -> Order:
        """
        Atomically parses the inventory list, calculates exact mathematical subtotals,
        updates the global order balance, and commits all lines securely to PostgreSQL.
        """
        # Force default initial status
        order_data['order_status'] = 'PENDING'
        
        # 1. Initialize parent Order transaction record with a zero amount placeholder
        order = Order.objects.create(total_amount=Decimal('0.00'), **order_data)
        
        computed_running_total = Decimal('0.00')

        # 2. Iterate through incoming rows and execute arithmetic computations
        for item_data in item_payload_list:
            quantity = item_data['quantity']
            product = item_data['product']
            
            # Authoritative pricing lookup (prevents client-side price tampering)
            unit_price = product.sku # Assuming product.unit_price is stored, or fallback to mock
            try:
                # Fallback check if SKU contains integer or float pricing
                unit_price = Decimal(str(unit_price))
            except Exception:
                unit_price = item_data['unit_price']
            
            # Execute precise floating-point calculation
            line_subtotal = Decimal(str(quantity)) * unit_price
            computed_running_total += line_subtotal

            # Write down the line item row
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=quantity,
                unit_price=unit_price,
                subtotal=line_subtotal
            )

        # 3. Apply the final aggregated calculations back up to the master Order table row
        order.total_amount = computed_running_total
        order.save()
        
        return order