from django.urls import path

from . import views

app_name = 'projects'

urlpatterns = [
    path('', views.project_list, name='list'),
    path('new/', views.project_create, name='create'),
    path('workers/', views.worker_list, name='worker_list'),
    path('workers/', views.worker_list, name='workers'),
    path('workers/new/', views.worker_create, name='worker_create'),
    path('workers/add/', views.worker_create, name='worker_add'),
    path('workers/<int:pk>/edit/', views.worker_update, name='worker_update'),
    path('workers/<int:pk>/edit/', views.worker_update, name='worker_edit'),
    path('workers/<int:pk>/delete/', views.worker_delete, name='worker_delete'),
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
