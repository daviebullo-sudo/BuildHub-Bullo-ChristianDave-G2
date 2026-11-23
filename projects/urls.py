from django.urls import path

from . import views

app_name = 'projects'

urlpatterns = [
    path('', views.project_list, name='list'),
    path('new/', views.project_create, name='create'),
    path('budget/', views.budget_list, name='budget_list'),
    path('<int:pk>/budget/', views.project_budget, name='budget_detail'),
    path('expenses/<int:pk>/delete/', views.expense_delete, name='expense_delete'),
    path('<int:pk>/', views.project_detail, name='detail'),
    path('<int:pk>/edit/', views.project_update, name='update'),
    path('<int:pk>/delete/', views.project_delete, name='delete'),
]
