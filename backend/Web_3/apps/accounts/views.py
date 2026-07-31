# apps/accounts/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login as django_login, logout as django_logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.urls import reverse

from apps.accounts.forms import EnterpriseOnboardingForm
from apps.accounts.services import StructuralOnboardingService
from apps.accounts.models import User
from apps.accounts.decorators import restrict_to_roles




@login_required(login_url='accounts:login')
def render_unified_dashboard(request):
    """Redirects the legacy accounts dashboard path directly to the consolidated SCM dashboard [18]."""
    return redirect('dashboard:home')

# ... rest of your account views remain completely preserved for backward compatibility ...
def render_onboarding_view(request):
    """Processes server-side template submission requests for company registration and user creation."""
    if request.method == "POST":
        form = EnterpriseOnboardingForm(request.POST)
        if form.is_valid():
            try:
                user = StructuralOnboardingService.execute_b2b_onboarding(form.cleaned_data)
                user.backend = 'django.contrib.auth.backends.ModelBackend'
                django_login(request, user)
                messages.success(request, "Enterprise application environment provisioned successfully.")
                # Redirects directly to the main consolidated dashboard [18]
                return redirect('dashboard:home')
            except Exception as e:
                messages.error(request, f"Onboarding collapsed: {str(e)}")
    else:
        form = EnterpriseOnboardingForm()
    return render(request, 'accounts/register.html', {'form': form})


def render_login_view(request):
    """Handles operator session initialization securely via Email authentication matches."""
    if request.method == "POST":
        id_key = request.POST.get('username')  
        phrase = request.POST.get('password')
        
        user = authenticate(request, email=id_key, password=phrase)
        
        if user is not None:
            if user.is_active and (user.company is None or getattr(user.company, 'is_verified', True)):
                django_login(request, user)
                
                next_url = request.GET.get('next')
                if next_url:
                    return redirect(next_url)
                # Redirects directly to the main consolidated dashboard [18]
                return redirect('dashboard:home')
            messages.error(request, "Access suspended. Check system tenant configuration.")
        else:
            messages.error(request, "Invalid security identifier or secret passphrase.")
            
    return render(request, 'accounts/login.html')




@login_required(login_url='accounts:login')
def inspect_operator_profile(request, operator_uuid):
    """Secures profile lookup pathways and prevents cross-tenant IDOR exploits."""
    target_operator = get_object_or_404(User, user_id=operator_uuid)
    
    if not request.user.is_staff and target_operator.company != request.user.company:
        messages.error(request, "Security violation: Cross-tenant tracking access denied.")
        return redirect('dashboard:home')
        
    can_edit = (request.user.user_id == target_operator.user_id) or (request.user.is_staff)
    
    if request.method == "POST":
        if not can_edit:
            messages.error(request, "You do not have permission to modify this profile.")
            return redirect('dashboard:home')
            
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        
        if email and email != target_operator.email:
            if User.objects.filter(email__iexact=email).exclude(user_id=target_operator.user_id).exists():
                messages.error(request, "An operational user account with this email address already exists.")
                return render(request, 'accounts/profile.html', {'target_operator': target_operator})
            target_operator.email = email
            
        if first_name: target_operator.first_name = first_name
        if last_name: target_operator.last_name = last_name
        if phone is not None: target_operator.phone = phone
        
        target_operator.save()
        messages.success(request, "Operator profile parameters updated successfully.")
        return redirect('accounts:operator_profile', operator_uuid=target_operator.user_id)

    return render(request, 'accounts/profile.html', {'target_operator': target_operator})


def logout_action(request):
    """Terminates session token state caches across active user loops."""
    django_logout(request)
    return redirect('accounts:login')


def render_password_reset_view(request):
    """Serves recovery verification and handles reset request generation securely."""
    if request.method == "POST":
        email = request.POST.get('email')
        try:
            user = User.objects.get(email__iexact=email)
            token = default_token_generator.make_token(user)
            uidb64 = urlsafe_base64_encode(force_bytes(user.user_id))
            
            reset_link = request.build_absolute_uri(
                reverse('accounts:password_reset_confirm', kwargs={'uidb64': uidb64, 'token': token})
            )
            
            send_mail(
                "Password Reset Request",
                f"Please click the link below to reset your password:\n{reset_link}",
                "admin@platform.com",
                [user.email],
                fail_silently=False,
            )
        except User.DoesNotExist:
            pass
            
        messages.success(request, "If an account matches that email, a recovery token link has been dispatched.")
        return redirect('accounts:login')

    return render(request, "accounts/forgot_password.html")


def render_password_reset_confirm_view(request, uidb64, token):
    """Processes validation challenges for password reset tokens."""
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(user_id=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        if request.method == "POST":
            new_password = request.POST.get('password')
            if new_password:
                user.set_password(new_password)
                user.save()
                messages.success(request, "Your password has been successfully reset. Please log in.")
                return redirect('accounts:login')
            else:
                messages.error(request, "Please enter a valid password.")
        return render(request, "accounts/password_reset_confirm.html", {'validlink': True})
    else:
        messages.error(request, "The password reset link is invalid or has expired.")
        return render(request, "accounts/password_reset_confirm.html", {'validlink': False})