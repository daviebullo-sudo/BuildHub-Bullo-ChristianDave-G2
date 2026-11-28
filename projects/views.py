import calendar
from datetime import date, timedelta
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from accounts.decorators import role_required
from accounts.models import User

from .forms import (
    ExpenseForm,
    MaterialForm,
    MaterialStatusForm,
    ProjectForm,
    ProjectStatusForm,
    ProjectTaskForm,
    WorkerForm,
)
from .models import Expense, Material, Project, ProjectTask, Worker


def visible_projects(user):
    """Projects a user may open: the ones they own or are assigned to."""
    return Project.objects.filter(Q(owner=user) | Q(contractor=user))


def budget_projects(user):
    if user.role == User.Role.CONTRACTOR:
        return Project.objects.filter(contractor=user)
    return Project.objects.filter(owner=user)


@login_required
def project_list(request):
    user = request.user
    if user.role == User.Role.CONTRACTOR:
        projects = Project.objects.filter(contractor=user)
    else:
        projects = Project.objects.filter(owner=user)

    selected_status = request.GET.get('status', '')
    if selected_status in Project.Status.values:
        projects = projects.filter(status=selected_status)

    context = {
        'projects': projects.select_related('owner', 'contractor'),
        'status_choices': Project.Status.choices,
        'selected_status': selected_status,
    }
    return render(request, 'projects/project_list.html', context)


@role_required(User.Role.HOMEOWNER)
def project_create(request):
    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.owner = request.user
            project.save()
            messages.success(request, 'Project created successfully.')
            return redirect('projects:detail', pk=project.pk)
        messages.error(request, 'Could not create the project. Please fix the errors below.')
    else:
        form = ProjectForm()
    return render(request, 'projects/project_form.html', {'form': form, 'is_edit': False})


@login_required
def project_detail(request, pk):
    # Not-found (404) for projects the user neither owns nor is assigned to.
    project = get_object_or_404(visible_projects(request.user), pk=pk)
    return render(
        request,
        'projects/project_detail.html',
        {'project': project, 'is_owner': project.owner_id == request.user.pk},
    )


@login_required
def progress_list(request):
    projects = visible_projects(request.user).prefetch_related('tasks').select_related(
        'owner', 'contractor'
    )
    return render(request, 'projects/progress_list.html', {'projects': projects})


@role_required(User.Role.CONTRACTOR)
def schedule(request):
    """Display a contractor's assigned projects and dated tasks by month."""
    month_value = request.GET.get('month', '')
    try:
        selected_month = date.fromisoformat(f'{month_value}-01')
    except (TypeError, ValueError):
        today = timezone.localdate()
        selected_month = today.replace(day=1)

    if selected_month.month == 12:
        next_month = selected_month.replace(year=selected_month.year + 1, month=1)
    else:
        next_month = selected_month.replace(month=selected_month.month + 1)
    if selected_month.month == 1:
        prev_month = selected_month.replace(year=selected_month.year - 1, month=12)
    else:
        prev_month = selected_month.replace(month=selected_month.month - 1)

    projects = (
        Project.objects.filter(contractor=request.user)
        .prefetch_related('tasks__worker')
        .select_related('owner')
    )
    month_start = selected_month
    month_end = selected_month.replace(
        day=calendar.monthrange(selected_month.year, selected_month.month)[1]
    )
    tasks = (
        ProjectTask.objects.filter(project__contractor=request.user, due_date__isnull=False)
        .filter(due_date__gte=month_start, due_date__lte=month_end)
        .select_related('project', 'worker')
        .order_by('due_date', 'project__title', 'title')
    )

    tasks_by_date = {}
    for task in tasks:
        tasks_by_date.setdefault(task.due_date, []).append(task)

    calendar_weeks = []
    calendar_start = month_start - timedelta(days=month_start.weekday())
    for week_number in range(6):
        week = []
        for day_number in range(7):
            day = calendar_start + timedelta(days=(week_number * 7) + day_number)
            week.append({
                'date': day,
                'in_month': day.month == selected_month.month,
                'is_today': day == timezone.localdate(),
                'tasks': tasks_by_date.get(day, []),
            })
        calendar_weeks.append(week)

    today = timezone.localdate()
    upcoming_tasks = (
        ProjectTask.objects.filter(
            project__contractor=request.user,
            due_date__gte=today,
        )
        .exclude(status=ProjectTask.Status.DONE)
        .select_related('project', 'worker')
        .order_by('due_date', 'project__title', 'title')[:8]
    )

    return render(request, 'projects/schedule.html', {
        'projects': projects,
        'tasks': tasks,
        'upcoming_tasks': upcoming_tasks,
        'calendar_weeks': calendar_weeks,
        'selected_month': selected_month,
        'month_name': selected_month.strftime('%B %Y'),
        'prev_month': prev_month.strftime('%Y-%m'),
        'next_month': next_month.strftime('%Y-%m'),
        'today': today,
    })


@login_required
def project_progress(request, pk):
    project = get_object_or_404(visible_projects(request.user), pk=pk)
    if request.method == 'POST':
        form = ProjectTaskForm(request.POST, project=project)
        if form.is_valid():
            task = form.save(commit=False)
            task.project = project
            task.created_by = request.user
            task.save()
            messages.success(request, 'Progress task added successfully.')
            return redirect('projects:progress_detail', pk=project.pk)
        messages.error(request, 'Could not add the progress task.')
    else:
        form = ProjectTaskForm(project=project)

    return render(request, 'projects/project_progress.html', {
        'project': project,
        'tasks': project.tasks.select_related('created_by'),
        'form': form,
        'status_form': ProjectStatusForm(instance=project),
    })


@login_required
@require_POST
def project_status_update(request, pk):
    project = get_object_or_404(visible_projects(request.user), pk=pk)
    form = ProjectStatusForm(request.POST, instance=project)
    if form.is_valid():
        form.save()
        messages.success(request, 'Project status updated.')
    else:
        messages.error(request, 'Could not update the project status.')
    return redirect('projects:progress_detail', pk=project.pk)


@login_required
@require_POST
def task_status_update(request, pk):
    task = get_object_or_404(
        ProjectTask.objects.select_related('project'),
        pk=pk,
        project__in=visible_projects(request.user),
    )
    status = request.POST.get('status')
    if status in ProjectTask.Status.values:
        task.status = status
        task.save(update_fields=['status', 'updated_at'])
        messages.success(request, 'Task status updated.')
    else:
        messages.error(request, 'Could not update the task status.')
    return redirect('projects:progress_detail', pk=task.project_id)


@login_required
def task_delete(request, pk):
    task = get_object_or_404(
        ProjectTask.objects.select_related('project'),
        pk=pk,
        project__in=visible_projects(request.user),
    )
    if request.method == 'POST':
        project_pk = task.project_id
        task.delete()
        messages.success(request, 'Progress task deleted.')
        return redirect('projects:progress_detail', pk=project_pk)
    return render(request, 'projects/task_confirm_delete.html', {'task': task})


@login_required
def budget_list(request):
    projects = budget_projects(request.user).annotate(
        spent=Sum('expenses__amount')
    ).select_related('owner', 'contractor')

    total_budget = sum((project.estimated_budget for project in projects), Decimal('0'))
    total_spent = sum((project.spent or Decimal('0') for project in projects), Decimal('0'))
    return render(request, 'projects/budget_list.html', {
        'projects': projects,
        'total_budget': total_budget,
        'total_spent': total_spent,
        'total_remaining': total_budget - total_spent,
    })


@login_required
def materials_list(request):
    projects = visible_projects(request.user).annotate(
        material_count=Count('materials')
    ).select_related('owner', 'contractor')
    return render(request, 'projects/materials_list.html', {'projects': projects})


@login_required
def project_materials(request, pk):
    project = get_object_or_404(visible_projects(request.user), pk=pk)
    if request.method == 'POST':
        form = MaterialForm(request.POST)
        if form.is_valid():
            material = form.save(commit=False)
            material.project = project
            material.created_by = request.user
            material.save()
            messages.success(request, 'Material added successfully.')
            return redirect('projects:materials_detail', pk=project.pk)
        messages.error(request, 'Could not add the material. Please fix the errors below.')
    else:
        form = MaterialForm()

    return render(request, 'projects/project_materials.html', {
        'project': project,
        'materials': project.materials.select_related('created_by'),
        'form': form,
        'status_choices': Material.Status.choices,
    })


@login_required
@require_POST
def material_update_status(request, pk):
    material = get_object_or_404(
        Material.objects.select_related('project'),
        pk=pk,
        project__in=visible_projects(request.user),
    )
    form = MaterialStatusForm(request.POST, instance=material)
    if form.is_valid():
        form.save()
        messages.success(request, 'Material status updated.')
    else:
        messages.error(request, 'Could not update the material status.')
    return redirect('projects:materials_detail', pk=material.project_id)


@login_required
def material_delete(request, pk):
    material = get_object_or_404(
        Material.objects.select_related('project'),
        pk=pk,
        project__in=visible_projects(request.user),
    )
    if request.method == 'POST':
        project_pk = material.project_id
        material.delete()
        messages.success(request, 'Material deleted.')
        return redirect('projects:materials_detail', pk=project_pk)
    return render(request, 'projects/material_confirm_delete.html', {'material': material})


@login_required
def project_budget(request, pk):
    project = get_object_or_404(visible_projects(request.user), pk=pk)
    if request.method == 'POST':
        form = ExpenseForm(request.POST)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.project = project
            expense.created_by = request.user
            expense.save()
            messages.success(request, 'Expense recorded successfully.')
            return redirect('projects:budget_detail', pk=project.pk)
        messages.error(request, 'Could not record the expense. Please fix the errors below.')
    else:
        form = ExpenseForm(initial={'date': timezone.localdate()})

    spent = project.expenses.aggregate(total=Sum('amount'))['total'] or Decimal('0')
    return render(request, 'projects/project_budget.html', {
        'project': project,
        'expenses': project.expenses.select_related('created_by'),
        'form': form,
        'spent': spent,
        'remaining': project.estimated_budget - spent,
    })


@login_required
def expense_delete(request, pk):
    expense = get_object_or_404(
        Expense.objects.select_related('project'),
        pk=pk,
        project__in=visible_projects(request.user),
    )
    if request.method == 'POST':
        project_pk = expense.project_id
        expense.delete()
        messages.success(request, 'Expense deleted.')
        return redirect('projects:budget_detail', pk=project_pk)
    return render(request, 'projects/expense_confirm_delete.html', {'expense': expense})


@role_required(User.Role.CONTRACTOR)
def worker_list(request):
    workers = Worker.objects.filter(contractor=request.user).annotate(
        task_count=Count('assigned_tasks')
    )
    return render(request, 'projects/worker_list.html', {'workers': workers})


@role_required(User.Role.CONTRACTOR)
def worker_create(request):
    if request.method == 'POST':
        form = WorkerForm(request.POST)
        if form.is_valid():
            worker = form.save(commit=False)
            worker.contractor = request.user
            worker.save()
            messages.success(request, 'Worker added successfully.')
            return redirect('projects:worker_list')
        messages.error(request, 'Could not add the worker. Please fix the errors below.')
    else:
        form = WorkerForm()
    return render(request, 'projects/worker_form.html', {
        'form': form,
        'is_edit': False,
    })


@role_required(User.Role.CONTRACTOR)
def worker_update(request, pk):
    worker = get_object_or_404(Worker, pk=pk, contractor=request.user)
    if request.method == 'POST':
        form = WorkerForm(request.POST, instance=worker)
        if form.is_valid():
            form.save()
            messages.success(request, 'Worker updated successfully.')
            return redirect('projects:worker_list')
        messages.error(request, 'Could not update the worker. Please fix the errors below.')
    else:
        form = WorkerForm(instance=worker)
    return render(request, 'projects/worker_form.html', {
        'form': form,
        'is_edit': True,
        'worker': worker,
    })


@role_required(User.Role.CONTRACTOR)
def worker_delete(request, pk):
    worker = get_object_or_404(Worker, pk=pk, contractor=request.user)
    if request.method == 'POST':
        worker.delete()
        messages.success(request, 'Worker removed successfully.')
        return redirect('projects:worker_list')
    return render(request, 'projects/worker_confirm_delete.html', {'worker': worker})


@role_required(User.Role.HOMEOWNER)
def project_update(request, pk):
    project = get_object_or_404(Project, pk=pk, owner=request.user)
    if request.method == 'POST':
        form = ProjectForm(request.POST, instance=project)
        if form.is_valid():
            form.save()
            messages.success(request, 'Project updated successfully.')
            return redirect('projects:detail', pk=project.pk)
        messages.error(request, 'Could not update the project. Please fix the errors below.')
    else:
        form = ProjectForm(instance=project)
    return render(
        request,
        'projects/project_form.html',
        {'form': form, 'is_edit': True, 'project': project},
    )


@role_required(User.Role.HOMEOWNER)
def project_delete(request, pk):
    project = get_object_or_404(Project, pk=pk, owner=request.user)
    if request.method == 'POST':
        title = project.title
        project.delete()
        messages.success(request, f'Project "{title}" was deleted.')
        return redirect('projects:list')
    return render(request, 'projects/project_confirm_delete.html', {'project': project})
