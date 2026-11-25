from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from accounts.decorators import role_required
from accounts.models import User

from .forms import ExpenseForm, MaterialForm, MaterialStatusForm, ProjectForm
from .models import Expense, Material, Project


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
