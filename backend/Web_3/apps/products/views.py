# apps/products/views.py
import uuid
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError as DjangoValidationError

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from apps.products.models import Product, ProductCategory, ProductStatusHistory
from apps.products.serializers import ProductDetailSerializer, ProductCreateUpdateSerializer, ProductCategorySerializer
from apps.products.selectors import ProductSelector
from apps.products.services import ProductService

from apps.companies.models import Company, CompanyType
from apps.companies.serializers import CompanyDetailSerializer
from apps.companies.selectors import CompanySelector

# =========================================================================
# 1. CORE HEADLESS REST API GATEWAYS (DRF Engine)
# =========================================================================

class CompanyDropdownViewSet(viewsets.ReadOnlyModelViewSet):
    """Provides secure, multi-tenant restricted corporate profile nodes to feed UI lookups."""
    serializer_class = CompanyDetailSerializer
    
    def get_queryset(self):
        return CompanySelector.get_visible_companies(self.request.user)


class ProductCategoryViewSet(viewsets.ModelViewSet):
    """Provides product categories to structure layout selection options safely."""
    queryset = ProductCategory.objects.all()
    serializer_class = ProductCategorySerializer


class ProductViewSet(viewsets.ModelViewSet):
    """
    Main programmatic interaction gateway for core supply chain commodities.
    Enforces multi-tenant query isolation to prevent IDOR cross-tenant data leaks.
    """
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['current_status', 'category']
    search_fields = ['product_name', 'sku', 'serial_number', 'batch_number']
    ordering_fields = ['created_at', 'product_name']
    ordering = ['-created_at']

    def get_queryset(self):
        return ProductSelector.get_visible_products(self.request.user)

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return ProductDetailSerializer
        return ProductCreateUpdateSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        
        # Enforce company ownership verification
        is_super = getattr(request.user, 'is_superuser', False) or getattr(request.user, 'is_staff', False)
        if not is_super:
            user_company = getattr(request.user, 'company', None)
            if not user_company:
                return Response({"detail": "User lacks associated company context."}, status=status.HTTP_400_BAD_REQUEST)
            validated_data['manufacturer_company_id'] = user_company.company_id

        try:
            # FIXED: Aligned primary key to .user_id
            product = ProductService.create_product(
                validated_data=validated_data,
                acting_user_id=request.user.user_id
            )
            return Response(ProductDetailSerializer(product).data, status=status.HTTP_201_CREATED)
        except DjangoValidationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], url_path='update-status')
    def update_status(self, request, pk=None):
        """Triggers lifecycle tracking transitions and appends transaction tracks atomically."""
        product = self.get_object()
        new_status = request.data.get('new_status')
        remarks = request.data.get('remarks')

        if not new_status:
            return Response({"error": "new_status payload parameter is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # FIXED: Aligned primary key to .user_id
            updated_product = ProductService.update_product_status(
                product=product,
                new_status=new_status,
                acting_user_id=request.user.user_id,
                remarks=remarks
            )
            return Response(ProductDetailSerializer(updated_product).data, status=status.HTTP_200_OK)
        except DjangoValidationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)


# =========================================================================
# 2. SERVER-SIDE WEB ADMINISTRATIVE DASHBOARD (DTL Channels)
# =========================================================================

@login_required
def product_list_html_view(request):
    """Renders all products visible within the user's active multi-tenant context."""
    products = ProductSelector.get_visible_products(request.user)
    context = {
        'product_list': products,
        'breadcrumbs': [{'title': 'Commodities Registry', 'url': '#'}]
    }
    return render(request, 'products/prod_list.html', context)


@login_required
def product_detail_html_view(request, product_id):
    """Renders deep nested auditing trace timelines for targeted commodity blocks."""
    visible_products = ProductSelector.get_visible_products(request.user)
    product = get_object_or_404(visible_products, product_id=product_id)
    
    context = {
        'product': product,
        'breadcrumbs': [
            {'title': 'Commodities Registry', 'url': '/products/list/'},
            {'title': 'Deep Lifecycle Trace Audit', 'url': '#'}
        ]
    }
    return render(request, 'products/prod_detail.html', context)


@login_required
def product_create_html_view(request):
    """Maps onboarding wizard forms cleanly into atomic service layers transaction routines."""
    error_messages = {}
    allowed_companies = CompanySelector.get_visible_companies(request.user)

    if request.method == 'POST':
        product_payload = {
            'manufacturer_company_id': request.POST.get('manufacturer_company_id'),
            'category_id': request.POST.get('category'),
            'product_name': request.POST.get('product_name'),
            'sku': request.POST.get('sku'),
            'serial_number': request.POST.get('serial_number'),
            'batch_number': request.POST.get('batch_number'),
            'manufacture_date': request.POST.get('manufacture_date') or None,
            'expiry_date': request.POST.get('expiry_date') or None,
            'description': request.POST.get('description'),
            'qr_code': request.POST.get('qr_code'),
            'current_status': 'MANUFACTURED' # Initial baseline lifecycle status
        }

        try:
            if product_payload['manufacturer_company_id']:
                product_payload['manufacturer_company_id'] = uuid.UUID(product_payload['manufacturer_company_id'])
            if product_payload['category_id']:
                product_payload['category'] = ProductCategory.objects.get(pk=product_payload.pop('category_id'))
        except (ValueError, ProductCategory.DoesNotExist):
            error_messages['global'] = "Data Validation Mismatch: Invalid category or company token provided."

        # Enforce secure company-ownership resolution
        is_super = getattr(request.user, 'is_superuser', False) or getattr(request.user, 'is_staff', False)
        if not is_super:
            user_company = getattr(request.user, 'company', None)
            if not user_company or user_company.company_id != product_payload['manufacturer_company_id']:
                error_messages['global'] = "Permission Denied: You cannot assign products to another company."

        if not error_messages:
            try:
                # FIXED: Aligned primary key to .user_id
                ProductService.create_product(product_payload, request.user.user_id)
                messages.success(request, "Commodity track node safely initialized.")
                return redirect('product_list')
            except DjangoValidationError as e:
                error_messages['global'] = str(e)
            except Exception as e:
                error_messages['global'] = f"Database Exception Refusal: {str(e)}"

    context = {
        'error_messages': error_messages,
        'categories': ProductCategory.objects.all(),
        'companies': allowed_companies,
        'breadcrumbs': [
            {'title': 'Commodities Registry', 'url': '/products/list/'},
            {'title': 'Initialize Fresh Commodity Node', 'url': '#'}
        ]
    }
    return render(request, 'products/prod_create.html', context)


@login_required
def product_update_html_view(request, product_id):
    """Modifies product attributes securely while updating status logs atomically."""
    visible_products = ProductSelector.get_visible_products(request.user)
    product = get_object_or_404(visible_products, product_id=product_id)
    error_messages = {}

    is_super = getattr(request.user, 'is_superuser', False) or getattr(request.user, 'is_staff', False)
    if not is_super:
        user_company = getattr(request.user, 'company', None)
        if not user_company or user_company.company_id != product.manufacturer_company_id:
            messages.error(request, "Permission Denied: You cannot modify products belonging to another company.")
            return redirect('product_list')

    if request.method == 'POST':
        new_status = request.POST.get('current_status')
        remarks = request.POST.get('remarks', 'Parameter configuration mutation update via dashboard form.')
        
        profile_update_data = {
            'product_name': request.POST.get('product_name'),
            'sku': request.POST.get('sku'),
            'batch_number': request.POST.get('batch_number'),
            'serial_number': request.POST.get('serial_number'),
            'description': request.POST.get('description'),
            'category_id': request.POST.get('category'),
            'manufacture_date': request.POST.get('manufacture_date') or None,
            'expiry_date': request.POST.get('expiry_date') or None,
        }

        try:
            if profile_update_data['category_id']:
                product.category = ProductCategory.objects.get(pk=profile_update_data['category_id'])
            
            # Process state transitions atomically
            if new_status and new_status != product.current_status:
                # FIXED: Aligned primary key to .user_id
                ProductService.update_product_status(product, new_status, request.user.user_id, remarks)

            product.product_name = profile_update_data['product_name']
            product.sku = profile_update_data['sku']
            product.batch_number = profile_update_data['batch_number']
            product.serial_number = profile_update_data['serial_number']
            product.description = profile_update_data['description']
            product.manufacture_date = profile_update_data['manufacture_date']
            product.expiry_date = profile_update_data['expiry_date']
            
            if product.manufacture_date and product.expiry_date and product.expiry_date < product.manufacture_date:
                raise DjangoValidationError("Expiry date cannot be prior to the manufacture date.")

            product.save()
            messages.success(request, f"Parameters successfully modified for {product.product_name}.")
            return redirect('product_detail', product_id=product.product_id)

        except ProductCategory.DoesNotExist:
            error_messages['global'] = "The specified product category does not exist."
        except DjangoValidationError as e:
            error_messages['global'] = str(e)
        except Exception as e:
            error_messages['global'] = f"An error occurred: {str(e)}"

    context = {
        'product': product,
        'categories': ProductCategory.objects.all(),
        'error_messages': error_messages,
        'breadcrumbs': [
            {'title': 'Commodities Registry', 'url': '/products/list/'},
            {'title': 'Configure Parameters Configuration', 'url': '#'}
        ]
    }
    return render(request, 'products/prod_update.html', context)