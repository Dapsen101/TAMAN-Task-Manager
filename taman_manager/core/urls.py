from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('accounts/register/', views.RegisterView, name='register'),
    path('accounts/login/', views.LoginView, name='login'),
    path('accounts/logout/', views.LogoutView, name='logout'),
    path('forgot-password/', views.ForgotPassword, name='forgot-password'),
    path('password-reset-sent/<str:reset_id>/', views.PasswordResetSent, name='password-reset-sent'),
    path('reset-password/<str:reset_id>/', views.ResetPassword, name='reset-password'),
    path('profile/', views.create_or_edit_profile, name='profile'),
    path('view-profile/', views.view_profile, name='view_profile'),
    path('settings/', views.settings_view, name='settings'),
    path('create-task/', views.create_task, name='create_task'),
    path('view-tasks/', views.view_tasks, name='view_tasks'),
    path('edit-task/<int:task_id>/', views.edit_task, name='edit_task'),
    path('update-status/<int:task_id>/', views.update_status, name='update_status')
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
 