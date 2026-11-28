from django.urls import path

from . import views

app_name = 'projects'

urlpatterns = [
    path('', views.project_list, name='list'),
    path('new/', views.project_create, name='create'),
    path('budget/', views.budget_list, name='budget_list'),
    path('materials/', views.materials_list, name='materials_list'),
    path('progress/', views.progress_list, name='progress_list'),
    path('<int:pk>/progress/', views.project_progress, name='progress_detail'),
    path('<int:pk>/progress/status/', views.project_status_update, name='project_status'),
    path('tasks/<int:pk>/status/', views.task_status_update, name='task_status'),
    path('tasks/<int:pk>/delete/', views.task_delete, name='task_delete'),
    path('<int:pk>/materials/', views.project_materials, name='materials_detail'),
    path('materials/<int:pk>/status/', views.material_update_status, name='material_status'),
    path('materials/<int:pk>/delete/', views.material_delete, name='material_delete'),
    path('<int:pk>/budget/', views.project_budget, name='budget_detail'),
    path('expenses/<int:pk>/delete/', views.expense_delete, name='expense_delete'),
    path('<int:pk>/', views.project_detail, name='detail'),
    path('<int:pk>/edit/', views.project_update, name='update'),
    path('<int:pk>/delete/', views.project_delete, name='delete'),
]
