from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import User

MAX_PHOTO_SIZE = 2 * 1024 * 1024  # 2 MB


class StyledFormMixin:
    """Adds the CSS class used by the templates to every non-radio widget."""

    def _style_fields(self):
        for field in self.fields.values():
            if not isinstance(field.widget, (forms.RadioSelect, forms.ClearableFileInput)):
                field.widget.attrs.setdefault('class', 'form-control')


class RegistrationForm(StyledFormMixin, UserCreationForm):
    first_name = forms.CharField(max_length=150, required=True)
    last_name = forms.CharField(max_length=150, required=True)
    email = forms.EmailField(required=True)
    role = forms.ChoiceField(
        choices=User.Role.choices,
        widget=forms.RadioSelect,
        initial=User.Role.HOMEOWNER,
        label='I am a',
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('first_name', 'last_name', 'username', 'email', 'role')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._style_fields()

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('An account with this email already exists.')
        return email


class LoginForm(StyledFormMixin, AuthenticationForm):
    error_messages = {
        'invalid_login': 'Invalid username or password. Please try again.',
        'inactive': 'This account is inactive.',
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._style_fields()


class ProfileForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'contact_number', 'profile_photo')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True
        self._style_fields()

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        taken = User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk)
        if taken.exists():
            raise forms.ValidationError('Another account already uses this email.')
        return email

    def clean_profile_photo(self):
        photo = self.cleaned_data.get('profile_photo')
        # Only newly uploaded files have a content_type; skip the existing/cleared value.
        if photo and hasattr(photo, 'content_type') and photo.size > MAX_PHOTO_SIZE:
            raise forms.ValidationError('Profile photo must be 2 MB or smaller.')
        return photo
