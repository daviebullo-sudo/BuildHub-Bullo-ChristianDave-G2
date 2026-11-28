from django import forms

from accounts.forms import StyledFormMixin
from accounts.models import User

from .models import Expense, Material, Project, ProjectTask


class ProjectForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Project
        fields = (
            'title',
            'description',
            'location',
            'estimated_budget',
            'start_date',
            'target_completion_date',
            'status',
            'contractor',
        )
        labels = {
            'estimated_budget': 'Estimated budget (PHP)',
            'target_completion_date': 'Target completion date',
            'contractor': 'Assigned contractor (optional)',
        }
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'estimated_budget': forms.NumberInput(attrs={'min': '0', 'step': '0.01'}),
            'start_date': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'target_completion_date': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only contractor accounts can be assigned to a project.
        self.fields['contractor'].queryset = User.objects.filter(role=User.Role.CONTRACTOR)
        self.fields['contractor'].empty_label = 'No contractor yet'
        self._style_fields()

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get('start_date')
        end = cleaned.get('target_completion_date')
        if start and end and end <= start:
            self.add_error(
                'target_completion_date',
                'Target completion date must be later than the start date.',
            )
        return cleaned


class ExpenseForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Expense
        fields = ('category', 'description', 'amount', 'date')
        labels = {
            'amount': 'Amount (PHP)',
        }
        widgets = {
            'description': forms.TextInput(attrs={'placeholder': 'What was purchased or paid for?'}),
            'amount': forms.NumberInput(attrs={'min': '0.01', 'step': '0.01'}),
            'date': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._style_fields()


class MaterialForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Material
        fields = ('name', 'quantity', 'unit', 'status')
        labels = {
            'quantity': 'Quantity',
            'unit': 'Unit (e.g. bags, pcs, m)',
        }
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'e.g. Ceramic floor tiles'}),
            'quantity': forms.NumberInput(attrs={'min': '0.01', 'step': '0.01'}),
            'unit': forms.TextInput(attrs={'placeholder': 'pcs'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._style_fields()


class MaterialStatusForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Material
        fields = ('status',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._style_fields()


class ProjectTaskForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = ProjectTask
        fields = ('title', 'description', 'due_date', 'status')
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'due_date': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._style_fields()


class ProjectStatusForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Project
        fields = ('status',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._style_fields()
