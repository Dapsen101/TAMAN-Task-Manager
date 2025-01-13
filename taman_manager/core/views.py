from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.core.mail import EmailMessage
from django.contrib.auth.forms import AuthenticationForm
from django.views.decorators.csrf import csrf_protect
from django.utils import timezone
from django.core.exceptions import ValidationError
from .forms import ProfileForm, TaskForm
from .models import Profile, PasswordReset, Task
from django.urls import reverse

@login_required
def dashboard(request):
    tasks_created = request.session.get('tasks_created', 0)
    tasks_in_progress = request.session.get('tasks_in_progress', 0)
    tasks_completed = request.session.get('tasks_completed', 0)

    profile, created = Profile.objects.get_or_create(user=request.user)
    return render(request, 'dashboard.html', {
        'profile': profile,
        'tasks_created': tasks_created,
        'tasks_in_progress': tasks_in_progress,
        'tasks_completed': tasks_completed,
    })



@csrf_protect
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
                validate_password(password)
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
            return redirect('login')

    return render(request, 'registration/register.html')


@csrf_protect
def LoginView(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('dashboard')
            else:
                messages.error(request, 'Invalid username or password.')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = AuthenticationForm()

    return render(request, 'registration/login.html', {'form': form})


@login_required
def LogoutView(request):
    logout(request)
    return redirect('login')


def ForgotPassword(request):
    if request.method == "POST":
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)
            new_password_reset = PasswordReset.objects.create(user=user)

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

    return render(request, 'registration/forgot_password.html')


def PasswordResetSent(request, reset_id):
    if PasswordReset.objects.filter(reset_id=reset_id).exists():
        return render(request, 'registration/password_reset_sent.html')
    else:
        messages.error(request, 'Invalid reset id')
        return redirect('forgot-password')


def ResetPassword(request, reset_id):
    try:
        password_reset = PasswordReset.objects.get(reset_id=reset_id)

        if request.method == "POST":
            password = request.POST.get('password')
            confirm_password = request.POST.get('confirm_password')

            if password != confirm_password:
                messages.error(request, 'Passwords do not match')
            elif len(password) < 5:
                messages.error(request, 'Password must be at least 5 characters long')
            else:
                expiration_time = password_reset.created_when + timezone.timedelta(minutes=10)
                if timezone.now() > expiration_time:
                    messages.error(request, 'Reset link has expired')
                    password_reset.delete()
                else:
                    user = password_reset.user
                    user.set_password(password)
                    user.save()
                    password_reset.delete()
                    messages.success(request, 'Password reset. Proceed to login')
                    return redirect('login')

    except PasswordReset.DoesNotExist:
        messages.error(request, 'Invalid reset id')
        return redirect('forgot-password')

    return render(request, 'registration/reset_password.html')


@login_required
def settings_view(request):
    return render(request, 'settings.html')


@login_required
def create_or_edit_profile(request):
    profile, created = Profile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        user = request.user

        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('view_profile')
    else:
        form = ProfileForm(instance=profile)

    return render(request, 'profile.html', {'form': form})


@login_required
def view_profile(request):
    profile = get_object_or_404(Profile, user=request.user)
    return render(request, 'view_profile.html', {'profile': profile})


@login_required
def create_task(request):
    if request.method == "POST":
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.created_by = request.user
            task.save()
            request.session['tasks_created'] = request.session.get('tasks_created', 0) + 1
            return redirect('view_tasks')
    else:
        form = TaskForm()

    return render(request, 'create_task.html', {'form': form})


@login_required
def view_tasks(request):
    tasks = Task.objects.filter(created_by=request.user)

    if request.method == "POST":
        task_id = request.POST.get("task_id")
        new_status = request.POST.get("status")
        assigned_user_id = request.POST.get("assigned_to")

        task = get_object_or_404(Task, id=task_id)

        if new_status:
            task.status = new_status
            task.save()
            if new_status == "In Progress":
                request.session['tasks_in_progress'] = request.session.get('tasks_in_progress', 0) + 1
            elif new_status == "Completed":
                request.session['tasks_completed'] = request.session.get('tasks_completed', 0) + 1

        if assigned_user_id:
            task.assigned_to_id = assigned_user_id
            task.save()

        return redirect('view_tasks')

    return render(request, 'view_task.html', {'tasks': tasks})


@login_required
def update_status(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    if request.method == 'POST':
        task.status = request.POST.get('status')
        task.save()
        return redirect('dashboard')


@login_required
def edit_task(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            return redirect('view_tasks')
    else:
        form = TaskForm(instance=task)

    users = User.objects.all()
    return render(request, 'edit_task.html', {'form': form, 'task': task, 'users': users})
