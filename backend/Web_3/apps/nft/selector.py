# apps/nft/selectors.py
from django.db.models import Q
from apps.nft.models import NFT

class NFTSelector:
    @staticmethod
    def get_visible_nfts(user):
        """
        Enforces strict company-level tenant isolation:
        - Staff/Superusers can inspect all minted assets.
        - Regular users can only access NFTs of products owned by their company.
        """
        if not user or user.is_anonymous:
            return NFT.objects.none()

        is_super = getattr(user, 'is_superuser', False) or getattr(user, 'is_staff', False)
        if is_super:
            return NFT.objects.all()

        user_company = getattr(user, 'company', None)
        if not user_company:
            return NFT.objects.none()

        return NFT.objects.filter(product__manufacturer_company_id=user_company.company_id)