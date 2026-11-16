from django.urls import path

from . import views

app_name = 'accounts'

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', views.UserLoginView.as_view(), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/homeowner/', views.homeowner_dashboard, name='homeowner_dashboard'),
    path('dashboard/contractor/', views.contractor_dashboard, name='contractor_dashboard'),
    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
]
