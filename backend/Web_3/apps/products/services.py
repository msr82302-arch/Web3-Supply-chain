import uuid
from django.db import transaction
from apps.products.models import Product, ProductCategory, ProductStatusHistory
from apps.companies.models import Company

class ProductService:
    @staticmethod
    @transaction.atomic
    def create_product(validated_data, acting_user_id: uuid.UUID) -> Product:
        """Atomically creates a product and records its initial state log."""
        product = Product.objects.create(**validated_data)
        
        # Drop the initial audit trace entry
        ProductStatusHistory.objects.create(
            product=product,
            changed_by=acting_user_id,
            old_status=None,
            new_status=product.current_status,
            remarks="Initial inventory provisioning lifecycle event logged."
        )
        return product

    @staticmethod
    @transaction.atomic
    def update_product_status(product: Product, new_status: str, acting_user_id: uuid.UUID, remarks: str = None) -> Product:
        """Safely updates a product state and appends an immutable timeline history log."""
        old_status = product.current_status
        if old_status == new_status:
            return product
            
        product.current_status = new_status
        product.save()

        ProductStatusHistory.objects.create(
            product=product,
            changed_by=acting_user_id,
            old_status=old_status,
            new_status=new_status,
            remarks=remarks or f"Status shifted from {old_status} to {new_status}."
        )
        return product


class CompanyService:
    @staticmethod
    @transaction.atomic
    def create_company(validated_data) -> Company:
        """Securely inserts a new enterprise profile into the unmanaged companies table."""
        return Company.objects.create(**validated_data)


class ProductCategoryService:
    @staticmethod
    @transaction.atomic
    def create_category(validated_data) -> ProductCategory:
        """Securely provisions a new product category asset classification."""
        return ProductCategory.objects.create(**validated_data)
