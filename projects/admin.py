from django.contrib import admin

from .models import Project


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'owner', 'contractor', 'status', 'estimated_budget', 'start_date')
    list_filter = ('status',)
    search_fields = ('title', 'owner__username')
