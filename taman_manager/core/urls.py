from django.urls import path
from . import views

urlpatterns = [

    path('', views.dashboard, name='dashboard'),
    path('accounts/register/', views.RegisterView, name='register'),
    path('accounts/login/', views.LoginView, name='login'),
    path('accounts/logout/', views.LogoutView, name='logout'),
    path('forgot-password/', views.ForgotPassword, name='forgot-password'),
    path('password-reset-sent/<str:reset_id>/', views.PasswordResetSent, name='password-reset-sent'),
    path('reset-password/<str:reset_id>/', views.ResetPassword, name='reset-password'),

    path('profile/', views.create_or_edit_profile, name='profile'),
    path('view_profile', views.view_profile, name='view_profile'),
    path('settings/', views.settings, name='settings'),
]