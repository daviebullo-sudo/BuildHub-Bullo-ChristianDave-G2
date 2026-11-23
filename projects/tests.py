from datetime import date
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from accounts.models import User

from .models import Expense, Project

PASSWORD = 'StrongPass#2026'


def make_user(username, role=User.Role.HOMEOWNER):
    return User.objects.create_user(
        username=username,
        email=f'{username}@example.com',
        password=PASSWORD,
        role=role,
        first_name=username.title(),
        last_name='Tester',
    )


def make_project(owner, title='Kitchen Remodel', contractor=None, **kwargs):
    defaults = {
        'estimated_budget': '150000.00',
        'start_date': date(2026, 12, 1),
        'target_completion_date': date(2027, 2, 1),
    }
    defaults.update(kwargs)
    return Project.objects.create(owner=owner, title=title, contractor=contractor, **defaults)


def form_data(**overrides):
    data = {
        'title': 'Bathroom Renovation',
        'description': 'Replace tiles and fixtures.',
        'location': 'Cebu City',
        'estimated_budget': '85000.00',
        'start_date': '2026-12-01',
        'target_completion_date': '2027-01-15',
        'status': Project.Status.PLANNING.value,
        'contractor': '',
    }
    data.update(overrides)
    return data


class ProjectCreateTests(TestCase):
    url = reverse('projects:create')

    def setUp(self):
        self.owner = make_user('owner')
        self.client.login(username='owner', password=PASSWORD)

    def test_homeowner_can_create_project(self):
        response = self.client.post(self.url, form_data(), follow=True)
        project = Project.objects.get(title='Bathroom Renovation')
        self.assertEqual(project.owner, self.owner)
        self.assertRedirects(response, reverse('projects:detail', args=[project.pk]))
        self.assertContains(response, 'Project created successfully')

    def test_can_assign_a_contractor(self):
        builder = make_user('builder', User.Role.CONTRACTOR)
        self.client.post(self.url, form_data(contractor=builder.pk))
        self.assertEqual(Project.objects.get().contractor, builder)

    def test_cannot_assign_a_homeowner_as_contractor(self):
        other = make_user('other', User.Role.HOMEOWNER)
        response = self.client.post(self.url, form_data(contractor=other.pk))
        self.assertIn('contractor', response.context['form'].errors)
        self.assertEqual(Project.objects.count(), 0)

    def test_required_fields(self):
        response = self.client.post(self.url, {})
        errors = response.context['form'].errors
        for field in ('title', 'estimated_budget', 'start_date', 'target_completion_date'):
            self.assertIn(field, errors)
        self.assertEqual(Project.objects.count(), 0)

    def test_target_date_must_be_after_start_date(self):
        response = self.client.post(
            self.url, form_data(start_date='2026-12-10', target_completion_date='2026-12-01')
        )
        self.assertContains(response, 'must be later than the start date')
        self.assertEqual(Project.objects.count(), 0)

    def test_budget_cannot_be_negative(self):
        response = self.client.post(self.url, form_data(estimated_budget='-5'))
        self.assertIn('estimated_budget', response.context['form'].errors)
        self.assertEqual(Project.objects.count(), 0)

    def test_contractor_cannot_create_projects(self):
        make_user('builder', User.Role.CONTRACTOR)
        self.client.login(username='builder', password=PASSWORD)
        response = self.client.post(self.url, form_data())
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Project.objects.count(), 0)

    def test_anonymous_user_is_sent_to_login(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertRedirects(
            response, f"{reverse('accounts:login')}?next={self.url}", fetch_redirect_response=False
        )


class ProjectReadTests(TestCase):
    def setUp(self):
        self.owner = make_user('owner')
        self.other_owner = make_user('other')
        self.builder = make_user('builder', User.Role.CONTRACTOR)
        self.stranger = make_user('stranger', User.Role.CONTRACTOR)
        self.mine = make_project(self.owner, 'My Kitchen', contractor=self.builder)
        self.theirs = make_project(self.other_owner, 'Their Garage')

    def test_homeowner_list_shows_only_own_projects(self):
        self.client.login(username='owner', password=PASSWORD)
        response = self.client.get(reverse('projects:list'))
        self.assertContains(response, 'My Kitchen')
        self.assertNotContains(response, 'Their Garage')

    def test_contractor_list_shows_only_assigned_projects(self):
        self.client.login(username='builder', password=PASSWORD)
        response = self.client.get(reverse('projects:list'))
        self.assertContains(response, 'My Kitchen')
        self.assertNotContains(response, 'Their Garage')

    def test_status_filter(self):
        make_project(self.owner, 'Done Deck', status=Project.Status.COMPLETED)
        self.client.login(username='owner', password=PASSWORD)
        response = self.client.get(reverse('projects:list'), {'status': 'completed'})
        self.assertContains(response, 'Done Deck')
        self.assertNotContains(response, 'My Kitchen')

    def test_owner_can_view_detail(self):
        self.client.login(username='owner', password=PASSWORD)
        response = self.client.get(reverse('projects:detail', args=[self.mine.pk]))
        self.assertContains(response, 'My Kitchen')
        self.assertContains(response, 'Edit')

    def test_assigned_contractor_can_view_but_not_edit_buttons(self):
        self.client.login(username='builder', password=PASSWORD)
        response = self.client.get(reverse('projects:detail', args=[self.mine.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, reverse('projects:update', args=[self.mine.pk]))

    def test_other_users_get_404(self):
        for username in ('other', 'stranger'):
            with self.subTest(user=username):
                self.client.login(username=username, password=PASSWORD)
                response = self.client.get(reverse('projects:detail', args=[self.mine.pk]))
                self.assertEqual(response.status_code, 404)


class ProjectUpdateDeleteTests(TestCase):
    def setUp(self):
        self.owner = make_user('owner')
        self.other_owner = make_user('other')
        self.builder = make_user('builder', User.Role.CONTRACTOR)
        self.project = make_project(self.owner, 'My Kitchen', contractor=self.builder)

    def test_owner_can_update(self):
        self.client.login(username='owner', password=PASSWORD)
        url = reverse('projects:update', args=[self.project.pk])
        response = self.client.post(
            url, form_data(title='Updated Kitchen', status=Project.Status.IN_PROGRESS.value), follow=True
        )
        self.assertRedirects(response, reverse('projects:detail', args=[self.project.pk]))
        self.project.refresh_from_db()
        self.assertEqual(self.project.title, 'Updated Kitchen')
        self.assertEqual(self.project.status, Project.Status.IN_PROGRESS)

    def test_update_validates_dates(self):
        self.client.login(username='owner', password=PASSWORD)
        url = reverse('projects:update', args=[self.project.pk])
        response = self.client.post(
            url, form_data(start_date='2027-03-01', target_completion_date='2027-01-01')
        )
        self.assertContains(response, 'must be later than the start date')
        self.project.refresh_from_db()
        self.assertEqual(self.project.title, 'My Kitchen')

    def test_other_homeowner_cannot_update_or_delete(self):
        self.client.login(username='other', password=PASSWORD)
        update_url = reverse('projects:update', args=[self.project.pk])
        delete_url = reverse('projects:delete', args=[self.project.pk])
        self.assertEqual(self.client.post(update_url, form_data(title='Hacked')).status_code, 404)
        self.assertEqual(self.client.post(delete_url).status_code, 404)
        self.project.refresh_from_db()
        self.assertEqual(self.project.title, 'My Kitchen')

    def test_assigned_contractor_cannot_update_or_delete(self):
        self.client.login(username='builder', password=PASSWORD)
        self.client.post(reverse('projects:update', args=[self.project.pk]), form_data(title='Hacked'))
        self.client.post(reverse('projects:delete', args=[self.project.pk]))
        self.project.refresh_from_db()
        self.assertEqual(self.project.title, 'My Kitchen')

    def test_delete_asks_for_confirmation_first(self):
        self.client.login(username='owner', password=PASSWORD)
        response = self.client.get(reverse('projects:delete', args=[self.project.pk]))
        self.assertContains(response, 'Delete project?')
        self.assertTrue(Project.objects.filter(pk=self.project.pk).exists())

    def test_owner_can_delete(self):
        self.client.login(username='owner', password=PASSWORD)
        response = self.client.post(reverse('projects:delete', args=[self.project.pk]), follow=True)
        self.assertRedirects(response, reverse('projects:list'))
        self.assertContains(response, 'was deleted')
        self.assertFalse(Project.objects.filter(pk=self.project.pk).exists())


class BudgetTests(TestCase):
    def setUp(self):
        self.owner = make_user('budget-owner')
        self.builder = make_user('budget-builder', User.Role.CONTRACTOR)
        self.stranger = make_user('budget-stranger', User.Role.CONTRACTOR)
        self.project = make_project(
            self.owner,
            'Budget Kitchen',
            contractor=self.builder,
            estimated_budget='100000.00',
        )

    def test_owner_and_contractor_can_view_and_add_expenses(self):
        for user in (self.owner, self.builder):
            with self.subTest(user=user.username):
                self.client.login(username=user.username, password=PASSWORD)
                detail_url = reverse('projects:budget_detail', args=[self.project.pk])
                response = self.client.post(detail_url, {
                    'category': Expense.Category.MATERIALS,
                    'description': 'Tiles',
                    'amount': '12500.50',
                    'date': '2026-12-02',
                }, follow=True)
                self.assertRedirects(response, detail_url)
                self.assertContains(response, 'Expense recorded successfully')

        expense = Expense.objects.first()
        self.assertEqual(expense.created_by, self.builder)
        response = self.client.get(detail_url)
        self.assertEqual(response.context['spent'], Decimal('25001.00'))

    def test_budget_summary_shows_totals(self):
        Expense.objects.create(
            project=self.project,
            category=Expense.Category.LABOR,
            description='Installation',
            amount='25000.00',
            date=date(2026, 12, 2),
            created_by=self.builder,
        )
        self.client.login(username='budget-owner', password=PASSWORD)
        response = self.client.get(reverse('projects:budget_list'))
        self.assertContains(response, 'PHP 100000.00')
        self.assertContains(response, 'PHP 25000.00')
        self.assertContains(response, 'PHP 75000.00')

    def test_unrelated_user_cannot_view_or_delete_expense(self):
        expense = Expense.objects.create(
            project=self.project,
            category=Expense.Category.OTHER,
            description='Delivery',
            amount='500.00',
            date=date(2026, 12, 2),
            created_by=self.owner,
        )
        self.client.login(username='budget-stranger', password=PASSWORD)
        detail_url = reverse('projects:budget_detail', args=[self.project.pk])
        self.assertEqual(self.client.get(detail_url).status_code, 404)
        self.assertEqual(
            self.client.post(reverse('projects:expense_delete', args=[expense.pk])).status_code,
            404,
        )
