from django.contrib import admin

from .models import Expense, Project


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'owner', 'contractor', 'status', 'estimated_budget', 'start_date')
    list_filter = ('status',)
    search_fields = ('title', 'owner__username')


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('description', 'project', 'category', 'amount', 'date', 'created_by')
    list_filter = ('category', 'date')
    search_fields = ('description', 'project__title')
