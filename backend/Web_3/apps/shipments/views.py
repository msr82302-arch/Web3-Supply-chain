# apps/shipments/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError as DjangoValidationError

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
# FIXED: Imported standard SessionAuthentication for session/test client compatibility
from rest_framework.authentication import SessionAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication

from apps.shipments.models import Shipment, ShipmentTracking
from apps.shipments.serializer import ShipmentDetailSerializer, ShipmentCreateSerializer, ShipmentTrackingSerializer
from apps.shipments.service import ShipmentService
from apps.shipments.selectors import ShipmentSelector
from apps.shipments.permission import IsShipmentParticipant

from apps.orders.models import Order
from apps.companies.models import Company

class ShipmentViewSet(viewsets.ModelViewSet):
    """Primary operational interface routing cargo, tracking carriers, and monitoring timelines."""
    # FIXED: Support both Session and JWT Authentication backends
    authentication_classes = [SessionAuthentication, JWTAuthentication]
    permission_classes = [IsAuthenticated, IsShipmentParticipant]

    def get_queryset(self):
        return ShipmentSelector.get_visible_shipments(self.request.user)

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return ShipmentDetailSerializer
        return ShipmentCreateSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            shipment = ShipmentService.initiate_shipment(serializer.validated_data)
            return Response(ShipmentDetailSerializer(shipment).data, status=status.HTTP_201_CREATED)
        except DjangoValidationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], url_path='log-telemetry')
    def log_telemetry(self, request, pk=None):
        """Custom endpoint allowing IoT or mobile clients to drop geographical coordinates."""
        shipment = self.get_object()
        
        # Enforce carrier RBAC checks (Only the assigned carrier can log pings)
        is_super = getattr(request.user, 'is_superuser', False) or getattr(request.user, 'is_staff', False)
        if not is_super:
            if shipment.logistics_company_id != request.user.company_id:
                return Response({"detail": "Access Denied: Only the assigned logistics carrier can log telemetry data."}, status=status.HTTP_403_FORBIDDEN)

        serializer = ShipmentTrackingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        serializer.validated_data.pop('shipment', None)
        telemetry = ShipmentService.append_gps_ping(shipment, serializer.validated_data)
        return Response(ShipmentTrackingSerializer(telemetry).data, status=status.HTTP_201_CREATED)


# =========================================================================
# SERVER SIDE WEB ADMINISTRATIVE HTML DASHBOARD RENDER CHANNELS (DTL)
# =========================================================================

@login_required
def shipment_list_html_view(request):
    """Renders active ecosystem organization grids available inside current user session view."""
    shipments = ShipmentSelector.get_visible_shipments(request.user).select_related('order', 'logistics_company')
    context = {
        'shipment_list': shipments,
        'breadcrumbs': [{'title': 'Logistics Terminal', 'url': '#'}]
    }
    return render(request, 'shipments/ship_list.html', context)


@login_required
def shipment_detail_html_view(request, shipment_id):
    """Renders exhaustive configuration profiles, historical variables, and tracking nodes."""
    visible_shipments = ShipmentSelector.get_visible_shipments(request.user)
    shipment = get_object_or_404(
        visible_shipments.select_related('order', 'logistics_company').prefetch_related('tracking_events'), 
        shipment_id=shipment_id
    )
    context = {
        'shipment': shipment,
        'breadcrumbs': [
            {'title': 'Logistics Terminal', 'url': '/shipments/'},
            {'title': 'Real-Time Telemetry Audit', 'url': '#'}
        ]
    }
    return render(request, 'shipments/ship_tracking.html', context)


@login_required
def shipment_create_html_view(request, order_id):
    """Allows authenticated sellers to initialize shipments from confirmed orders."""
    order = get_object_or_404(Order, order_id=order_id)
    error_messages = {}

    is_super = getattr(request.user, 'is_superuser', False) or getattr(request.user, 'is_staff', False)
    if not is_super:
        if order.seller_company_id != request.user.company_id:
            messages.error(request, "Permission Denied: You can only create shipments for your own sales orders.")
            return redirect('order_list')

    if request.method == 'POST':
        shipment_number = request.POST.get('shipment_number')
        logistics_company_id = request.POST.get('logistics_company')
        expected_arrival = request.POST.get('expected_arrival') or None

        try:
            shipment = ShipmentService.initiate_shipment({
                'order': order,
                'logistics_company_id': logistics_company_id,
                'shipment_number': shipment_number,
                'expected_arrival': expected_arrival,
                'shipment_status': 'MANIFEST_CREATED'
            })
            messages.success(request, f"Shipment {shipment_number} successfully registered.")
            return redirect('shipment_list')
        except Exception as e:
            error_messages['global'] = f"Shipment Initialization Halted: {str(e)}"

    context = {
        'order': order,
        'carriers': Company.objects.filter(company_type='LOGISTICS_PROVIDER', is_verified=True),
        'error_messages': error_messages,
        'breadcrumbs': [
            {'title': 'Logistics Terminal', 'url': '/shipments/'},
            {'title': 'Initialize Waypoint Dispatch', 'url': '#'}
        ]
    }
    return render(request, 'shipments/ship_create.html', context)


@login_required
def shipment_update_html_view(request, shipment_id):
    """Allows carriers to update transit milestones and register waypoints."""
    visible_shipments = ShipmentSelector.get_visible_shipments(request.user)
    shipment = get_object_or_404(visible_shipments, shipment_id=shipment_id)
    error_messages = {}

    is_super = getattr(request.user, 'is_superuser', False) or getattr(request.user, 'is_staff', False)
    if not is_super:
        if shipment.logistics_company_id != request.user.company_id:
            messages.error(request, "Permission Denied: Only the assigned carrier can update this shipment.")
            return redirect('shipment_list')

    if request.method == 'POST':
        new_status = request.POST.get('shipment_status')
        location = request.POST.get('location')
        latitude = request.POST.get('latitude')
        longitude = request.POST.get('longitude')

        try:
            if new_status and new_status != shipment.shipment_status:
                shipment.shipment_status = new_status
                if new_status == 'DELIVERED':
                    shipment.actual_arrival = timezone.now().date()
                shipment.save()

            if location and latitude and longitude:
                ShipmentService.append_gps_ping(shipment, {
                    'location': location,
                    'latitude': latitude,
                    'longitude': longitude,
                    'tracking_status': new_status or shipment.shipment_status
                })

            messages.success(request, "Telemetry waypoints logged successfully.")
            return redirect('shipment_detail', shipment_id=shipment.shipment_id)
        except Exception as e:
            error_messages['global'] = f"Tracking Log Failed: {str(e)}"

    context = {
        'shipment': shipment,
        'error_messages': error_messages,
        'breadcrumbs': [
            {'title': 'Logistics Terminal', 'url': '/shipments/'},
            {'title': 'Configure Waypoint Parameters', 'url': '#'}
        ]
    }
    return render(request, 'shipments/ship_update.html', context)