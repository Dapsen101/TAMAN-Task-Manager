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
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.http import JsonResponse
from datetime import datetime, timedelta
from .forms import ProfileForm, TaskForm
from .models import Profile, PasswordReset, Task
from django.urls import reverse


@login_required
def dashboard(request):
    """Enhanced dashboard with real analytics and metrics"""
    user = request.user
    profile, created = Profile.objects.get_or_create(user=user)
    
    # Get all user's tasks
    all_tasks = Task.objects.filter(created_by=user)
    
    # Calculate metrics
    total_tasks = all_tasks.count()
    completed_tasks = all_tasks.filter(status='Completed').count()
    pending_tasks = all_tasks.filter(status__in=['Created', 'In Progress']).count()
    in_progress_tasks = all_tasks.filter(status='In Progress').count()
    
    # Time-based metrics
    now = timezone.now()
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)
    
    tasks_this_week = all_tasks.filter(created_at__gte=week_ago).count()
    tasks_this_month = all_tasks.filter(created_at__gte=month_ago).count()
    completed_this_week = all_tasks.filter(
        status='Completed',
        completed_at__isnull=False,
        completed_at__gte=week_ago
    ).count()
    
    # Productivity score (completed tasks / total tasks * 100)
    productivity_score = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
    completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
    
    # Category breakdown
    category_breakdown = all_tasks.values('category').annotate(count=Count('id')).order_by('-count')
    
    # Recent tasks
    recent_tasks = all_tasks[:5]
    
    # Analytics data for charts
    # Weekly productivity (last 7 days)
    weekly_data = []
    for i in range(6, -1, -1):
        date = now - timedelta(days=i)
        day_start = timezone.make_aware(datetime.combine(date.date(), datetime.min.time()))
        day_end = day_start + timedelta(days=1)
        completed_count = all_tasks.filter(
            status='Completed',
            completed_at__isnull=False,
            completed_at__gte=day_start,
            completed_at__lt=day_end
        ).count()
        weekly_data.append({
            'date': date.strftime('%Y-%m-%d'),
            'day': date.strftime('%a'),
            'count': completed_count
        })
    
    # Monthly summary (last 6 months)
    monthly_data = []
    for i in range(5, -1, -1):
        month_start = now.replace(day=1) - timedelta(days=30*i)
        month_end = (month_start + timedelta(days=32)).replace(day=1)
        month_tasks = all_tasks.filter(created_at__gte=month_start, created_at__lt=month_end)
        monthly_data.append({
            'month': month_start.strftime('%b %Y'),
            'completed': month_tasks.filter(status='Completed').count(),
            'pending': month_tasks.filter(status__in=['Created', 'In Progress']).count()
        })
    
    # Task completion over time (last 30 days)
    completion_over_time = []
    for i in range(29, -1, -1):
        date = now - timedelta(days=i)
        day_start = timezone.make_aware(datetime.combine(date.date(), datetime.min.time()))
        day_end = day_start + timedelta(days=1)
        completed_count = all_tasks.filter(
            status='Completed',
            completed_at__isnull=False,
            completed_at__gte=day_start,
            completed_at__lt=day_end
        ).count()
        completion_over_time.append({
            'date': date.strftime('%Y-%m-%d'),
            'count': completed_count
        })
    
    context = {
        'profile': profile,
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'pending_tasks': pending_tasks,
        'in_progress_tasks': in_progress_tasks,
        'tasks_this_week': tasks_this_week,
        'tasks_this_month': tasks_this_month,
        'completed_this_week': completed_this_week,
        'productivity_score': round(productivity_score, 1),
        'completion_rate': round(completion_rate, 1),
        'category_breakdown': category_breakdown,
        'recent_tasks': recent_tasks,
        'weekly_data': weekly_data,
        'monthly_data': monthly_data,
        'completion_over_time': completion_over_time,
    }
    
    return render(request, 'dashboard.html', context)


@csrf_protect
def RegisterView(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
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
            Profile.objects.create(user=user, full_name=username, email=email)
            messages.success(request, 'Account created successfully. Please login.')
            return redirect('login')

    return render(request, 'registration/register.html')


@csrf_protect
def LoginView(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {username}!')
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
    messages.success(request, 'You have been logged out successfully.')
    return redirect('login')


def ForgotPassword(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
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
                settings.EMAIL_HOST_USER if hasattr(settings, 'EMAIL_HOST_USER') else 'noreply@taskmanager.com',
                [email]
            )
            email_message.fail_silently = True
            email_message.send()

            return redirect('password-reset-sent', reset_id=new_password_reset.reset_id)

        except User.DoesNotExist:
            messages.error(request, f"No user with email '{email}' found")

    return render(request, 'registration/forgotpassword.html')


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
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('view_profile')
        else:
            messages.error(request, 'Please correct the errors below.')
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
            messages.success(request, f'Task "{task.name}" created successfully!')
            return redirect('view_tasks')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = TaskForm()
        # Filter users to show only relevant ones
        form.fields['assigned_to'].queryset = User.objects.all()

    return render(request, 'create_task.html', {'form': form})


@login_required
def view_tasks(request):
    """Enhanced task view with search, filter, sort, and pagination"""
    tasks = Task.objects.filter(created_by=request.user)
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        tasks = tasks.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(milestone__icontains=search_query)
        )
    
    # Filter by status
    status_filter = request.GET.get('status', '')
    if status_filter:
        tasks = tasks.filter(status=status_filter)
    
    # Filter by category
    category_filter = request.GET.get('category', '')
    if category_filter:
        tasks = tasks.filter(category=category_filter)
    
    # Sort functionality
    sort_by = request.GET.get('sort', '-created_at')
    if sort_by in ['name', '-name', 'status', '-status', 'category', '-category', 'created_at', '-created_at', 'due_date', '-due_date']:
        tasks = tasks.order_by(sort_by)
    else:
        tasks = tasks.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(tasks, 10)  # Show 10 tasks per page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'tasks': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
        'category_filter': category_filter,
        'sort_by': sort_by,
    }
    
    return render(request, 'view_task.html', context)


@login_required
def update_status(request, task_id):
    task = get_object_or_404(Task, id=task_id, created_by=request.user)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(Task.STATUS_CHOICES):
            task.status = new_status
            task.save()
            messages.success(request, f'Task status updated to {new_status}')
        else:
            messages.error(request, 'Invalid status')
        return redirect('view_tasks')
    return redirect('view_tasks')


@login_required
def edit_task(request, task_id):
    task = get_object_or_404(Task, id=task_id, created_by=request.user)
    
    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            messages.success(request, f'Task "{task.name}" updated successfully!')
            return redirect('view_tasks')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = TaskForm(instance=task)
        form.fields['assigned_to'].queryset = User.objects.all()
    
    return render(request, 'edit_task.html', {'form': form, 'task': task})


@login_required
def delete_task(request, task_id):
    """Delete task functionality"""
    task = get_object_or_404(Task, id=task_id, created_by=request.user)
    
    if request.method == 'POST':
        task_name = task.name
        task.delete()
        messages.success(request, f'Task "{task_name}" deleted successfully!')
        return redirect('view_tasks')
    
    return render(request, 'delete_task.html', {'task': task})


@login_required
def analytics_api(request):
    """API endpoint for analytics data"""
    user = request.user
    all_tasks = Task.objects.filter(created_by=user)
    
    # Weekly productivity data
    weekly_data = []
    now = timezone.now()
    for i in range(6, -1, -1):
        date = now - timedelta(days=i)
        day_start = timezone.make_aware(datetime.combine(date.date(), datetime.min.time()))
        day_end = day_start + timedelta(days=1)
        completed_count = all_tasks.filter(
            status='Completed',
            completed_at__isnull=False,
            completed_at__gte=day_start,
            completed_at__lt=day_end
        ).count()
        weekly_data.append({
            'date': date.strftime('%Y-%m-%d'),
            'day': date.strftime('%a'),
            'count': completed_count
        })
    
    # Category distribution
    category_data = list(all_tasks.values('category').annotate(count=Count('id')))
    
    return JsonResponse({
        'weekly_data': weekly_data,
        'category_data': category_data,
    })
