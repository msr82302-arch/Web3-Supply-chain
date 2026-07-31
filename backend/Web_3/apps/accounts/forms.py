from django import forms
from apps.accounts.models import User

class EnterpriseOnboardingForm(forms.ModelForm):
    """Processes corporate account initialization fields without non-existent username hooks."""
    
    company_name = forms.CharField(max_length=255)
    company_type = forms.ChoiceField(
        choices=[
            ('MANUFACTURER', 'Manufacturer'), 
            ('LOGISTICS', 'Logistics Provider'), 
            ('BUYER', 'NFT Buyer/Customer'), 
            ('AUDITOR', 'Auditor')
        ]
    )
    registration_number = forms.CharField(max_length=100)
    tax_number = forms.CharField(max_length=100)
    
    password = forms.CharField(widget=forms.PasswordInput())

    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'phone']