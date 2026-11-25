from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import F, Q
from django.urls import reverse


class Project(models.Model):
    """A renovation project owned by a homeowner and optionally assigned to a contractor."""

    class Status(models.TextChoices):
        PLANNING = 'planning', 'Planning'
        IN_PROGRESS = 'in_progress', 'In Progress'
        ON_HOLD = 'on_hold', 'On Hold'
        COMPLETED = 'completed', 'Completed'

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='projects'
    )
    contractor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_projects',
        limit_choices_to={'role': 'contractor'},
    )
    title = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    location = models.CharField(max_length=200, blank=True)
    estimated_budget = models.DecimalField(
        max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0'))]
    )
    start_date = models.DateField()
    target_completion_date = models.DateField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PLANNING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.CheckConstraint(
                condition=Q(target_completion_date__gt=F('start_date')),
                name='project_target_after_start',
            ),
            models.CheckConstraint(
                condition=Q(estimated_budget__gte=0),
                name='project_budget_not_negative',
            ),
        ]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('projects:detail', args=[self.pk])

    @property
    def remaining_budget(self):
        spent = getattr(self, 'spent', None) or Decimal('0')
        return self.estimated_budget - spent


class Expense(models.Model):
    class Category(models.TextChoices):
        LABOR = 'labor', 'Labor'
        MATERIALS = 'materials', 'Materials'
        EQUIPMENT = 'equipment', 'Equipment'
        PERMITS = 'permits', 'Permits'
        UTILITIES = 'utilities', 'Utilities'
        OTHER = 'other', 'Other'

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='expenses')
    category = models.CharField(max_length=20, choices=Category.choices, default=Category.MATERIALS)
    description = models.CharField(max_length=200)
    amount = models.DecimalField(
        max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))]
    )
    date = models.DateField()
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='recorded_expenses'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-created_at']
        constraints = [
            models.CheckConstraint(
                condition=Q(amount__gte=Decimal('0.01')),
                name='expense_amount_positive',
            ),
        ]

    def __str__(self):
        return f'{self.description} - PHP {self.amount}'


class Material(models.Model):
    class Status(models.TextChoices):
        PLANNED = 'planned', 'Planned'
        ORDERED = 'ordered', 'Ordered'
        PURCHASED = 'purchased', 'Purchased'

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='materials')
    name = models.CharField(max_length=200)
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
    )
    unit = models.CharField(max_length=30, default='pcs')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PLANNED)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='recorded_materials'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['status', 'name']
        constraints = [
            models.CheckConstraint(
                condition=Q(quantity__gte=Decimal('0.01')),
                name='material_quantity_positive',
            ),
        ]

    def __str__(self):
        return f'{self.name} ({self.quantity} {self.unit})'
