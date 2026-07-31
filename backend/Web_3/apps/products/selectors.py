# apps/products/selectors.py
from django.db.models import Q
from apps.products.models import Product

class ProductSelector:
    @staticmethod
    def get_visible_products(user):
        """
        Enforces strict multi-tenant boundaries:
        - System superusers/global staff can access all products.
        - Regular users are limited strictly to products belonging to their own company.
        """
        if not user or user.is_anonymous:
            return Product.objects.none()
            
        is_super = getattr(user, 'is_superuser', False) or getattr(user, 'is_staff', False)
        if is_super:
            return Product.objects.all()

        user_company = getattr(user, 'company', None)
        if not user_company:
            return Product.objects.none()

        return Product.objects.filter(manufacturer_company_id=user_company.company_id)