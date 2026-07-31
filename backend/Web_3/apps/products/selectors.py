# apps/products/selectors.py
from django.db.models import Q
from apps.products.models import Product

class ProductSelector:
    @staticmethod
    def get_visible_products(user):
        """
        Enforces strict multi-tenant boundaries [22]:
        - System superusers/global staff can access all products.
        - Manufacturers are limited strictly to products belonging to their own company [22].
        - Buyers, Carriers, and Auditors can view active verified products globally [22].
        """
        if not user or user.is_anonymous:
            return Product.objects.none()