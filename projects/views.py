from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from accounts.decorators import role_required
from accounts.models import User

from .forms import ProjectForm
from .models import Project


def visible_projects(user):
    """Projects a user may open: the ones they own or are assigned to."""
    return Project.objects.filter(Q(owner=user) | Q(contractor=user))


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
