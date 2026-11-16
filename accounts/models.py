from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models

contact_number_validator = RegexValidator(
    regex=r'^\+?[0-9 \-]{7,20}$',
    message='Enter a valid contact number (digits, spaces, dashes, optional leading +).',
)


class User(AbstractUser):
    """BuildHub user. Passwords are hashed by Django's built-in authentication."""

    class Role(models.TextChoices):
        HOMEOWNER = 'homeowner', 'Homeowner'
        CONTRACTOR = 'contractor', 'Contractor'

    email = models.EmailField('email address', unique=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.HOMEOWNER)
    contact_number = models.CharField(
        max_length=20, blank=True, validators=[contact_number_validator]
    )
    profile_photo = models.ImageField(upload_to='profile_photos/', blank=True)

    def __str__(self):
        return self.username

    @property
    def display_name(self):
        return self.get_full_name() or self.username
