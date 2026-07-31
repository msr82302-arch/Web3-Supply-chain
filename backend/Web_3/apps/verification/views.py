# apps/verification/views.py
import uuid
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError as DjangoValidationError

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from apps.verification.models import QRCode, VerificationLog
from apps.verification.serializer import QRCodeDetailSerializer, QRCodeCreateSerializer, VerificationLogSerializer
from apps.verification.service import VerificationService
from apps.verification.selector import VerificationSelector
from apps.verification.permission import IsVerificationParticipant
from apps.products.selectors import ProductSelector

class QRCodeViewSet(viewsets.ModelViewSet):
    """Primary operational interface tracking item QR tags and scanning authentication metrics."""
    permission_classes = [IsAuthenticated, IsVerificationParticipant]

    def get_queryset(self):
        # FIXED: Enforced company tenant filtering on querysets
        return VerificationSelector.get_visible_qr_codes(self.request.user)

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return QRCodeDetailSerializer
        return QRCodeCreateSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        
        # Enforce tenancy checks on product manufacturer
        is_super = getattr(request.user, 'is_superuser', False) or getattr(request.user, 'is_staff', False)
        if not is_super:
            product = validated_data.get('product')
            if product.manufacturer_company_id != request.user.company_id:
                return Response({"detail": "Access Denied: Product belongs to another company."}, status=status.HTTP_403_FORBIDDEN)

        qr_code = VerificationService.issue_qr_label(validated_data)
        return Response(QRCodeDetailSerializer(qr_code).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='scan')
    def process_scan(self, request, pk=None):
        """
        Public/Enterprise scan endpoint. Auto-intercepts client hardware profiles 
        and IP parameters straight out of incoming HTTP headers.
        """
        qr = self.get_object()
        user_agent = request.META.get('HTTP_USER_AGENT', 'Unknown Scanner Client')
        
        # Extract client IP safely
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(',')[0].strip()
        else:
            ip_address = request.META.get('REMOTE_ADDR', '127.0.0.1')

        serializer = VerificationLogSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Inject metadata parameters server-side
        serializer.validated_data['ip_address'] = ip_address
        serializer.validated_data['device_info'] = user_agent
        
        # FIXED: Securely resolve the verified_by actor from request session
        if request.user and request.user.is_authenticated:
            serializer.validated_data['verified_by'] = request.user.user_id

        log_entry = VerificationService.log_scan_event(qr, serializer.validated_data)
        return Response(VerificationLogSerializer(log_entry).data, status=status.HTTP_201_CREATED)


# =========================================================================
# SERVER SIDE WEB ADMINISTRATIVE HTML DASHBOARD RENDER CHANNELS (DTL)
# =========================================================================

def public_verification_html_view(request, qr_id):
    """
    Public consumer-facing verification scan endpoint [1].
    Validates the dynamic cryptographic signature to prove product authenticity [1].
    """
    qr = get_object_or_404(QRCode, qr_id=qr_id)
    sig = request.GET.get('sig')
    ts = request.GET.get('ts')

    user_agent = request.META.get('HTTP_USER_AGENT', 'Unknown Consumer Client')
    ip_address = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', '127.0.0.1'))
    if ',' in ip_address:
        ip_address = ip_address.split(',')[0].strip()

    # Capture location metadata if provided by client JavaScript coordinates
    lat = request.GET.get('lat')
    lng = request.GET.get('lng')

    scan_metadata = {
        'ip_address': ip_address,
        'device_info': user_agent,
        'latitude': lat,
        'longitude': lng,
        'country': request.GET.get('country', 'N/A'),
        'city': request.GET.get('city', 'N/A'),
    }

    if request.user and request.user.is_authenticated:
        scan_metadata['verified_by'] = request.user.user_id

    # Cryptographically verify the signature
    log_entry = VerificationService.verify_dynamic_qr_code(qr, sig, ts, scan_metadata)
    
    context = {
        'qr': qr,
        'log_entry': log_entry,
        'is_authentic': log_entry.verification_result == 'SUCCESS',
        'breadcrumbs': [{'title': 'Product Authenticity Verification', 'url': '#'}]
    }
    return render(request, 'verification/public_verify.html', context)


@login_required
def verification_dashboard_html_view(request):
    """Renders active SCM verification scan logs restricted to your company context."""
    # FIXED: Enforced strict company tenant boundaries
    logs = VerificationSelector.get_visible_verification_logs(request.user).order_by('-verified_at')
    context = {
        'scan_logs': list(logs),
        'breadcrumbs': [{'title': 'Ecosystem Verification Ledger', 'url': '#'}]
    }
    return render(request, 'verification/verify_dashboard.html', context)