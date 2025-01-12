from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.core.mail import EmailMessage
from django.contrib.auth.forms import AuthenticationForm
from django.views.decorators.csrf import csrf_protect
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .forms import ProfileForm
from .models import Profile
from django.urls import reverse
from .models import *

# Require login to access the home page
@login_required
def dashboard(request):
    profile = Profile.objects.get(user=request.user)
    return render(request, 'dashboard.html', {'profile': profile})



def RegisterView(request):
    if request.method == "POST":
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        user_data_has_error = False

        if User.objects.filter(username=username).exists():
            user_data_has_error = True
            messages.error(request, 'Username already exists')

        if User.objects.filter(email=email).exists():
            user_data_has_error = True
            messages.error(request, 'Email already exists')

        if password != confirm_password:
            user_data_has_error = True
            messages.error(request, 'Passwords do not match')

        if len(password) < 5:
            user_data_has_error = True
            messages.error(request, 'Password must be at least 5 characters')

        if not user_data_has_error:
            try:
                validate_password(password)  # Django's built-in password validation
            except ValidationError as e:
                user_data_has_error = True
                messages.error(request, e.messages[0])

        if not user_data_has_error:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password
            )
            login(request, user)
            messages.success(request, 'Account created successfully. Please complete your profile.')
            return redirect('profile')

    return render(request, 'registration/register.html')

# # def RegisterView(request):
#     if request.method == "POST":
#         username = request.POST.get('username')
#         email = request.POST.get('email')
#         password = request.POST.get('password')
#         confirm_password = request.POST.get('confirm_password')

#         user_data_has_error = False

#         if User.objects.filter(username=username).exists():
#             user_data_has_error = True
#             messages.error(request, 'Username already exists')

#         if User.objects.filter(email=email).exists():
#             user_data_has_error = True
#             messages.error(request, 'Email already exists')

#         # Ensure password is at least 5 characters long
#         if len(password) < 5:
#             user_data_has_error = True
#             messages.error(request, 'Password must be at least 5 characters')

#         if password != confirm_password:
#             user_data_has_error = True
#             messages.error(request, 'Passwords do not match')

#         if not user_data_has_error:
#             # Create the user and log them in automatically
#             user = User.objects.create_user(
#                 username=username,
#                 email=email,
#                 password=password
#             )
#             login(request, user)
#             messages.success(request, 'Account created successfully. Please complete your profile.')
#             return redirect('create-profile')  # Redirect to the profile creation page

#     return render(request, 'registration/register.html')


# CSRF Protection, optional, as it's enabled by default in Django
@csrf_protect
def LoginView(request):
    # Check if the form is submitted via POST
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        
        # If form is valid, authenticate and log in the user
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            
            # Authenticate the user
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                login(request, user)  # Log the user in
                return redirect('dashboard')  # Redirect to the dashboard or the desired page
            else:
                # Handle invalid login attempt
                return render(request, 'registration/login.html', {'form': form, 'error': 'Invalid username or password.'})
        else:
            # If the form is not valid, render the form again with error messages
            return render(request, 'registration/login.html', {'form': form})
    else:
        # If GET request, show the empty form
        form = AuthenticationForm()
        return render(request, 'registration/login.html', {'form': form})


# def LoginView(request):
#     username = None
#     password = None

#     if request.method == 'POST':
#         username = request.POST.get('username')
#         password = request.POST.get('password')

#         user = authenticate(request=request, username=username, password=password)
#         if user is not None:
#             login(request, user)
#             return redirect('dashboard')
#         else:
#             messages.error(request, 'Invalid username or password')
#             return redirect('login')

#     return render(request, 'registration/login.html')

def LogoutView(request):
    logout(request)
    return redirect('login')

def ForgotPassword(request):
    if request.method == "POST":
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)
            new_password_reset = PasswordReset(user=user)
            new_password_reset.save()

            password_reset_url = reverse('reset-password', kwargs={'reset_id': new_password_reset.reset_id})
            full_password_reset_url = f'{request.scheme}://{request.get_host()}{password_reset_url}'

            email_body = f'Reset your password using the link below:\n\n{full_password_reset_url}'
            email_message = EmailMessage(
                'Reset your password',
                email_body,
                settings.EMAIL_HOST_USER,
                [email]
            )
            email_message.fail_silently = True
            email_message.send()

            return redirect('password-reset-sent', reset_id=new_password_reset.reset_id)

        except User.DoesNotExist:
            messages.error(request, f"No user with email '{email}' found")
            return redirect('forgot-password')

    return render(request, 'registration/forgot_password.html')

def PasswordResetSent(request, reset_id):
    if PasswordReset.objects.filter(reset_id=reset_id).exists():
        return render(request, 'registration/password_reset_sent.html')
    else:
        messages.error(request, 'Invalid reset id')
        return redirect('forgot-password')

def ResetPassword(request, reset_id):
    try:
        password_reset_id = PasswordReset.objects.get(reset_id=reset_id)

        if request.method == "POST":
            password = request.POST.get('password')
            confirm_password = request.POST.get('confirm_password')

            passwords_have_error = False

            if password != confirm_password:
                passwords_have_error = True
                messages.error(request, 'Passwords do not match')

            if len(password) < 5:
                passwords_have_error = True
                messages.error(request, 'Password must be at least 5 characters long')

            expiration_time = password_reset_id.created_when + timezone.timedelta(minutes=10)
            if timezone.now() > expiration_time:
                passwords_have_error = True
                messages.error(request, 'Reset link has expired')
                password_reset_id.delete()

            if not passwords_have_error:
                user = password_reset_id.user
                user.set_password(password)
                user.save()
                password_reset_id.delete()
                messages.success(request, 'Password reset. Proceed to login')
                return redirect('login')
            else:
                return redirect('reset-password', reset_id=reset_id)

    except PasswordReset.DoesNotExist:
        messages.error(request, 'Invalid reset id')
        return redirect('forgot-password')

    return render(request, 'registration/reset_password.html')

@login_required
def settings(request):
    return render(request, 'settings.html')


# views.py
@login_required
def create_or_edit_profile(request):
    try:
        profile = request.user.profile
    except Profile.DoesNotExist:
        profile = None

    if request.method == 'POST':
        if profile:
            form = ProfileForm(request.POST, request.FILES, instance=profile)
        else:
            form = ProfileForm(request.POST, request.FILES)

        if form.is_valid():
            form.save()
            return redirect('view_profile')  # Redirect to view profile after saving

    else:
        form = ProfileForm(instance=profile)

    return render(request, 'profile.html', {'form': form})

@login_required
def view_profile(request):
    try:
        profile = request.user.profile  # Fetch the user's profile
    except Profile.DoesNotExist:
        profile = None  # Handle case where profile doesn't exist

    return render(request, 'view_profile.html', {'profile': profile})