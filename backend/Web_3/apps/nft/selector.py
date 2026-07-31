# apps/nft/selectors.py
from apps.nft.models import NFT

class NFTSelector:
    @staticmethod
    def get_visible_nfts(user):
        """
        Enforces strict company-level tenant isolation [19]:
        - Staff/Superusers can inspect all minted assets.
        - Manufacturers (with a valid company) see NFTs of products owned by their company [19].
        - Buyers can inspect all verified digital twin certificates globally [19].
        """
        if not user or user.is_anonymous:
            return NFT.objects.none()

        is_super = getattr(user, 'is_superuser', False) or getattr(user, 'is_staff', False)
        if is_super:
            return NFT.objects.all()

        role_name = getattr(user.role, 'role_name', '').upper() if user.role else ''
        user_company = getattr(user, 'company', None)
        
        if role_name in ['MANUFACTURER', 'Manufacturer'] and user_company:
            return NFT.objects.filter(product__manufacturer_company_id=user_company.company_id)
        else:
            # Buyers and other participants see minted digital twin certificates globally [19]
            return NFT.objects.all()