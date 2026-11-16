from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

User = get_user_model()
PASSWORD = 'StrongPass#2026'


def make_user(username='juan', role=User.Role.HOMEOWNER, email=None):
    return User.objects.create_user(
        username=username,
        email=email or f'{username}@example.com',
        password=PASSWORD,
        role=role,
        first_name='Test',
        last_name='User',
    )


class RegistrationTests(TestCase):
    url = reverse('accounts:register')

    def data(self, **overrides):
        data = {
            'first_name': 'Juan',
            'last_name': 'Dela Cruz',
            'username': 'juandc',
            'email': 'juan@example.com',
            'role': User.Role.HOMEOWNER.value,
            'password1': PASSWORD,
            'password2': PASSWORD,
        }
        data.update(overrides)
        return data

    def test_register_success_hashes_password(self):
        response = self.client.post(self.url, self.data(), follow=True)
        self.assertRedirects(response, reverse('accounts:login'))
        self.assertContains(response, 'Account created successfully')
        user = User.objects.get(username='juandc')
        self.assertNotEqual(user.password, PASSWORD)
        self.assertTrue(user.password.startswith('pbkdf2_sha256$'))
        self.assertTrue(user.check_password(PASSWORD))
        self.assertEqual(user.role, User.Role.HOMEOWNER)

    def test_register_contractor_role(self):
        self.client.post(self.url, self.data(role=User.Role.CONTRACTOR.value))
        self.assertEqual(User.objects.get(username='juandc').role, User.Role.CONTRACTOR)

    def test_required_fields(self):
        response = self.client.post(self.url, {})
        self.assertEqual(response.status_code, 200)
        errors = response.context['form'].errors
        for field in ('first_name', 'last_name', 'username', 'email', 'role', 'password1', 'password2'):
            self.assertIn(field, errors)
        self.assertEqual(User.objects.count(), 0)

    def test_invalid_email_format(self):
        response = self.client.post(self.url, self.data(email='not-an-email'))
        self.assertIn('email', response.context['form'].errors)
        self.assertEqual(User.objects.count(), 0)

    def test_duplicate_username(self):
        make_user(username='juandc', email='other@example.com')
        response = self.client.post(self.url, self.data())
        self.assertIn('username', response.context['form'].errors)
        self.assertEqual(User.objects.count(), 1)

    def test_duplicate_email_is_case_insensitive(self):
        make_user(username='someone', email='juan@example.com')
        response = self.client.post(self.url, self.data(email='JUAN@Example.com'))
        self.assertContains(response, 'already exists')
        self.assertEqual(User.objects.count(), 1)

    def test_password_confirmation_must_match(self):
        response = self.client.post(self.url, self.data(password2='DifferentPass#2026'))
        self.assertIn('password2', response.context['form'].errors)
        self.assertEqual(User.objects.count(), 0)

    def test_weak_password_rejected(self):
        response = self.client.post(self.url, self.data(password1='12345678', password2='12345678'))
        self.assertIn('password2', response.context['form'].errors)
        self.assertEqual(User.objects.count(), 0)


class LoginLogoutTests(TestCase):
    login_url = reverse('accounts:login')

    def test_login_homeowner_goes_to_homeowner_dashboard(self):
        make_user('owner', User.Role.HOMEOWNER)
        response = self.client.post(
            self.login_url, {'username': 'owner', 'password': PASSWORD}, follow=True
        )
        self.assertRedirects(response, reverse('accounts:homeowner_dashboard'))
        self.assertContains(response, 'Homeowner Dashboard')

    def test_login_contractor_goes_to_contractor_dashboard(self):
        make_user('builder', User.Role.CONTRACTOR)
        response = self.client.post(
            self.login_url, {'username': 'builder', 'password': PASSWORD}, follow=True
        )
        self.assertRedirects(response, reverse('accounts:contractor_dashboard'))
        self.assertContains(response, 'Contractor Dashboard')

    def test_invalid_credentials_show_error(self):
        make_user('owner')
        response = self.client.post(self.login_url, {'username': 'owner', 'password': 'wrong'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Invalid username or password')
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_logout_ends_session(self):
        make_user('owner')
        self.client.login(username='owner', password=PASSWORD)
        response = self.client.post(reverse('accounts:logout'), follow=True)
        self.assertRedirects(response, self.login_url)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_logout_requires_post(self):
        make_user('owner')
        self.client.login(username='owner', password=PASSWORD)
        response = self.client.get(reverse('accounts:logout'))
        self.assertEqual(response.status_code, 405)
        self.assertIn('_auth_user_id', self.client.session)


class ProtectedPageTests(TestCase):
    def test_anonymous_users_are_sent_to_login(self):
        for name in (
            'dashboard',
            'homeowner_dashboard',
            'contractor_dashboard',
            'profile',
            'profile_edit',
        ):
            with self.subTest(page=name):
                url = reverse(f'accounts:{name}')
                response = self.client.get(url)
                self.assertRedirects(
                    response,
                    f"{reverse('accounts:login')}?next={url}",
                    fetch_redirect_response=False,
                )


class RoleDashboardTests(TestCase):
    def test_homeowner_cannot_open_contractor_dashboard(self):
        make_user('owner', User.Role.HOMEOWNER)
        self.client.login(username='owner', password=PASSWORD)
        response = self.client.get(reverse('accounts:contractor_dashboard'), follow=True)
        self.assertRedirects(response, reverse('accounts:homeowner_dashboard'))
        self.assertContains(response, 'do not have access')
        self.assertNotContains(response, 'Contractor Dashboard')

    def test_contractor_cannot_open_homeowner_dashboard(self):
        make_user('builder', User.Role.CONTRACTOR)
        self.client.login(username='builder', password=PASSWORD)
        response = self.client.get(reverse('accounts:homeowner_dashboard'), follow=True)
        self.assertRedirects(response, reverse('accounts:contractor_dashboard'))
        self.assertContains(response, 'do not have access')

    def test_each_role_sees_its_own_navigation(self):
        make_user('owner', User.Role.HOMEOWNER)
        self.client.login(username='owner', password=PASSWORD)
        response = self.client.get(reverse('accounts:homeowner_dashboard'))
        self.assertContains(response, 'My Projects')
        self.assertNotContains(response, 'Assigned Jobs')


class ProfileTests(TestCase):
    edit_url = reverse('accounts:profile_edit')

    def setUp(self):
        self.user = make_user('owner')
        self.client.login(username='owner', password=PASSWORD)

    def edit_data(self, **overrides):
        data = {
            'first_name': 'Juan',
            'last_name': 'Dela Cruz',
            'email': 'owner@example.com',
            'contact_number': '+63 912 345 6789',
        }
        data.update(overrides)
        return data

    def test_view_own_profile(self):
        response = self.client.get(reverse('accounts:profile'))
        self.assertContains(response, 'owner@example.com')
        self.assertContains(response, 'Homeowner')

    def test_update_profile(self):
        response = self.client.post(self.edit_url, self.edit_data(), follow=True)
        self.assertRedirects(response, reverse('accounts:profile'))
        self.assertContains(response, 'Your profile has been updated')
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Juan')
        self.assertEqual(self.user.contact_number, '+63 912 345 6789')

    def test_cannot_use_another_users_email(self):
        make_user('other', email='taken@example.com')
        response = self.client.post(self.edit_url, self.edit_data(email='taken@example.com'))
        self.assertIn('email', response.context['form'].errors)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'owner@example.com')

    def test_invalid_contact_number(self):
        response = self.client.post(self.edit_url, self.edit_data(contact_number='abc'))
        self.assertIn('contact_number', response.context['form'].errors)

    def test_editing_only_changes_own_profile(self):
        other = make_user('other')
        self.client.post(self.edit_url, self.edit_data(first_name='Changed'))
        other.refresh_from_db()
        self.assertEqual(other.first_name, 'Test')
        self.assertNotEqual(self.user.pk, other.pk)
