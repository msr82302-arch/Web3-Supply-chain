# apps/companies/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.core.exceptions import ValidationError as DjangoValidationError
from django.contrib.auth.decorators import login_required

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.pagination import PageNumberPagination

from apps.companies.models import Company, CompanyStatus, CompanyType
from apps.companies.serializers import CompanyDetailSerializer, CompanyCreateUpdateSerializer, CompanyAddressSerializer
from apps.companies.service import CompanyService
from apps.companies.selectors import CompanySelector
from apps.companies.permissions import IsCompanyNetworkParticipant

class StandardCompanyResultsPagination(PageNumberPagination):
    """Enforces standardized page limits across high-throughput data lists."""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class CompanyViewSet(viewsets.ModelViewSet):
    """
    Main programmatic endpoint matrix for Web3 corporate profile nodes.
    Protects mutations via permissions checking and handles query multitenancy.
    """
    permission_classes = [IsCompanyNetworkParticipant]
    pagination_class = StandardCompanyResultsPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    filterset_fields = ['status', 'company_type', 'is_verified']
    search_fields = ['company_name', 'registration_number', 'tax_number', 'email']
    ordering_fields = ['created_at', 'company_name']
    ordering = ['-created_at']

    def get_queryset(self):
        return CompanySelector.get_visible_companies(self.request.user)

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return CompanyDetailSerializer
        return CompanyCreateUpdateSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        addresses_data = validated_data.get('addresses', [])
        try:
            company = CompanyService.create_company_with_channels(
                company_data=validated_data,
                creator_user_id=request.user.user_id,
                addresses_data=addresses_data
            )
            return Response(CompanyDetailSerializer(company).data, status=status.HTTP_201_CREATED)
        except DjangoValidationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        addresses_data = validated_data.get('addresses', None)
        try:
            company = CompanyService.update_company_profile(
                company=instance,
                profile_data=validated_data,
                locations_payload=addresses_data
            )
            return Response(CompanyDetailSerializer(company).data, status=status.HTTP_200_OK)
        except DjangoValidationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], url_path='add-address')
    def add_address(self, request, pk=None):
        company = self.get_object()
        serializer = CompanyAddressSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            new_address = CompanyService.append_secure_address(
                company=company,
                address_data=serializer.validated_data,
                executing_user_id=request.user.user_id
            )
            return Response(CompanyAddressSerializer(new_address).data, status=status.HTTP_201_CREATED)
        except DjangoValidationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], url_path='verify-status')
    def verify_status(self, request, pk=None):
        company = self.get_object()
        target_status = request.data.get('status')
        try:
            updated_company = CompanyService.transition_compliance_lifecycle(
                company=company,
                target_status=target_status,
                authority_user=request.user
            )
            return Response(CompanyDetailSerializer(updated_company).data, status=status.HTTP_200_OK)
        except DjangoValidationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)


# =========================================================================
# SERVER SIDE WEB ADMINISTRATIVE HTML DASHBOARD RENDER CHANNELS (DTL)
# =========================================================================

@login_required
def company_list_html_view(request):
    """Renders active ecosystem organization grids available inside current user session view."""
    companies = CompanySelector.get_visible_companies(request.user)
    context = {
        'company_list': companies,
        'breadcrumbs': [{'title': 'Ecosystem Registry', 'url': '#'}]
    }
    return render(request, 'companies/com_list.html', context)


@login_required
def company_detail_html_view(request, company_id):
    """Renders exhaustive configuration profiles, historical variables, and tracking nodes."""
    visible = CompanySelector.get_visible_companies(request.user)
    company = get_object_or_404(visible, company_id=company_id)
    context = {
        'company': company,
        'breadcrumbs': [
            {'title': 'Entity Node Index', 'url': '/companies/'},
            {'title': 'Cryptographic Specification Audit', 'url': '#'}
        ]
    }
    return render(request, 'companies/com_detail.html', context)


@login_required
def company_update_html_view(request, company_id):
    """Allows tenant administrators or system superusers to modify corporate configuration fields."""
    visible = CompanySelector.get_visible_companies(request.user)
    company = get_object_or_404(visible, company_id=company_id)
    
    role_ctx = CompanySelector.get_user_role_context(request.user.user_id, company.company_id)
    
    # FIXED: Defensively checking roles via getattr to prevent SimpleLazyObject lookup errors
    is_super = getattr(request.user, 'is_superuser', False) or getattr(request.user, 'is_staff', False)
    is_admin = role_ctx and getattr(role_ctx, 'is_company_admin', False)

    if not (is_super or is_admin):
        messages.error(request, "Execution Refusal: Account lacks administrative write privileges for this tenant.")
        return redirect('/companies/')

    if request.method == 'POST':
        profile_data = {
            'company_name': request.POST.get('company_name'),
            'company_type': request.POST.get('company_type'),
            'registration_number': request.POST.get('registration_number'),
            'tax_number': request.POST.get('tax_number'),
            'email': request.POST.get('email'),
            'phone': request.POST.get('phone'),
            'website': request.POST.get('website'),
            'logo_url': request.POST.get('logo_url'),
        }
        try:
            CompanyService.update_company_profile(company, profile_data)
            messages.success(request, f"Parameters successfully modified for {company.company_name}.")
            return redirect('/companies/')
        except Exception as e:
            messages.error(request, f"Modification Error: {str(e)}")

    context = {
        'company': company,
        'breadcrumbs': [
            {'title': 'Entity Node Index', 'url': '/companies/'},
            {'title': 'Parameter Modifications Configuration', 'url': '#'}
        ]
    }
    return render(request, 'companies/com_update.html', context)


@login_required
def company_create_html_view(request):
    """Maps onboarding forms straight into structural database transactional blocks."""
    error_message = None
    if request.method == 'POST':
        company_data = {
            'company_name': request.POST.get('company_name'),
            'registration_number': request.POST.get('registration_number'),
            'company_type': request.POST.get('company_type', CompanyType.BUYER),
            'tax_number': request.POST.get('tax_number'),
            'email': request.POST.get('email'),
            'phone': request.POST.get('phone'),
            'website': request.POST.get('website'),
        }
        try:
            CompanyService.create_company_with_channels(
                company_data=company_data,
                creator_user_id=request.user.user_id,
                addresses_data=[]
            )
            messages.success(request, "Enterprise onboarding successfully initialized.")
            return redirect('/companies/')
        except Exception as e:
            error_message = f"Deployment Refusal: {str(e)}"

    context = {
        'error_message': error_message,
        'breadcrumbs': [
            {'title': 'Entity Node Index', 'url': '/companies/'},
            {'title': 'Initialize Fresh Node Instance', 'url': '#'}
        ]
    }
    return render(request, 'companies/com_create.html', context)