# apps/orders/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError as DjangoValidationError

from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from apps.orders.models import Order, OrderItem
from apps.companies.models import Company
from apps.orders.serializer import OrderDetailSerializer, OrderCreateSerializer
from apps.orders.services import OrderService
from apps.orders.selector import OrderSelector
from apps.orders.permission import IsOrderParticipant
from apps.products.selectors import ProductSelector # Imported product selectors

class OrderViewSet(viewsets.ModelViewSet):
    """Primary endpoint handling sales processing, invoices, and purchase records."""
    permission_classes = [IsAuthenticated, IsOrderParticipant]

    def get_queryset(self):
        return OrderSelector.get_visible_orders(self.request.user)

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return OrderDetailSerializer
        return OrderCreateSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        
        is_super = getattr(request.user, 'is_superuser', False) or getattr(request.user, 'is_staff', False)
        if not is_super:
            validated_data['buyer_company'] = request.user.company
        
        items_data = validated_data.pop('items', [])
        try:
            order = OrderService.process_new_invoice(
                order_data=validated_data,
                item_payload_list=items_data
            )
            return Response(OrderDetailSerializer(order).data, status=status.HTTP_201_CREATED)
        except DjangoValidationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)


# =========================================================================
# SERVER SIDE WEB ADMINISTRATIVE HTML DASHBOARD RENDER CHANNELS (DTL)
# =========================================================================

@login_required
def order_list_html_view(request):
    """Renders active ecosystem organization grids available inside current user session view."""
    orders = OrderSelector.get_visible_orders(request.user).select_related('buyer_company', 'seller_company').prefetch_related('items')
    context = {
        'order_list': orders,
        'breadcrumbs': [{'title': 'Procurement Ledger', 'url': '#'}]
    }
    return render(request, 'orders/orders-track.html', context)


@login_required
def order_detail_html_view(request, order_id):
    """Renders exhaustive configuration profiles, historical variables, and tracking nodes."""
    visible_orders = OrderSelector.get_visible_orders(request.user)
    order = get_object_or_404(
        visible_orders.select_related('buyer_company', 'seller_company').prefetch_related('items__product'), 
        order_id=order_id
    )
    context = {
        'order': order,
        'breadcrumbs': [
            {'title': 'Procurement Ledger', 'url': '/orders/list/'},
            {'title': 'Cryptographic Invoice Audit', 'url': '#'}
        ]
    }
    return render(request, 'orders/orders-detail.html', context)


@login_required
def order_create_html_view(request):
    """Maps onboarding forms straight into structural database transactional blocks."""
    error_messages = {}
    
    if request.method == 'POST':
        buyer_company_id = request.POST.get('buyer_company')
        seller_company_id = request.POST.get('seller_company')
        order_number = request.POST.get('order_number')
        order_status = 'PENDING'
        expected_delivery = request.POST.get('expected_delivery') or None
        
        is_super = getattr(request.user, 'is_superuser', False) or getattr(request.user, 'is_staff', False)
        if not is_super:
            user_company = getattr(request.user, 'company', None)
            user_company_id = str(user_company.company_id) if user_company else None
            if user_company_id != buyer_company_id:
                error_messages['global'] = "Permission Denied: You cannot issue purchase orders for another company."

        if buyer_company_id == seller_company_id:
            error_messages['seller_company'] = "The buyer company and seller company cannot be the same enterprise entity."
            
        if not error_messages:
            try:
                order = Order.objects.create(
                    buyer_company_id=buyer_company_id,
                    seller_company_id=seller_company_id,
                    order_number=order_number,
                    order_status=order_status,
                    total_amount=0.00,  
                    order_date=timezone.now(),
                    expected_delivery=expected_delivery
                )
                return redirect('order_list')
            except Exception as e:
                error_messages['global'] = f"Invoice Manifest Rejected: {str(e)}"
                
    context = {
        'error_messages': error_messages,
        'companies': Company.objects.filter(is_verified=True),
        # FIXED: Pass visible products to populate the dynamic line-item builder on the UI
        'products': ProductSelector.get_visible_products(request.user),
        'breadcrumbs': [
            {'title': 'Procurement Ledger', 'url': '/orders/list/'},
            {'title': 'Initialize Procurement Node', 'url': '#'}
        ]
    }
    return render(request, 'orders/orders-create.html', context)


@login_required
def order_update_html_view(request, order_id):
    """Allows tenant administrators or system superusers to modify corporate configuration fields."""
    visible_orders = OrderSelector.get_visible_orders(request.user)
    order = get_object_or_404(visible_orders, order_id=order_id)
    error_messages = {}
    
    user_company = getattr(request.user, 'company', None)
    is_super = getattr(request.user, 'is_superuser', False) or getattr(request.user, 'is_staff', False)

    if request.method == 'POST':
        new_status = request.POST.get('order_status')
        old_status = order.order_status
        
        if new_status and new_status != old_status:
            try:
                user_company_uuid = getattr(user_company, 'company_id', None)
                if new_status in ['APPROVED', 'COMPLETED'] and not is_super:
                    if order.seller_company_id != user_company_uuid:
                        raise DjangoValidationError("Only the seller company can approve or process this order.")
                order.order_status = new_status
            except DjangoValidationError as e:
                error_messages['global'] = str(e)

        order_number = request.POST.get('order_number')
        expected_delivery = request.POST.get('expected_delivery') or None
        
        if not error_messages:
            try:
                order.order_number = order_number
                order.expected_delivery = expected_delivery
                order.save()
                messages.success(request, f"Parameters successfully modified for Order {order.order_number}.")
                return redirect('order_list')
            except Exception as e:
                error_messages['global'] = f"Database Sync Error: {str(e)}"
            
    context = {
        'order': order,
        'error_messages': error_messages,
        'breadcrumbs': [
            {'title': 'Procurement Ledger', 'url': '/orders/list/'},
            {'title': 'Modify Order parameters', 'url': '#'}
        ]
    }
    return render(request, 'orders/orders-update.html', context)