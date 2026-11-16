from django import forms

from accounts.forms import StyledFormMixin
from accounts.models import User

from .models import Project


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
