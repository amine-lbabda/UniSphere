
from django.utils import timezone
from collaboration.models import Task


def get_project_tasks(project):
    return Task.objects.filter(
        project=project
    ).order_by('deadline')


def search_tasks(project, keyword):
    tasks = get_project_tasks(project)

    if not keyword or not keyword.strip():
        return tasks

    return tasks.filter(
        title__icontains=keyword.strip()
    )


def filter_tasks(project, status=None, priority=None):
    tasks = get_project_tasks(project)

    valid_statuses = [
        'todo',
        'in_progress',
        'review',
        'completed'
    ]

    valid_priorities = [
        'low',
        'medium',
        'high',
        'urgent'
    ]

    if status:
        if status not in valid_statuses:
            raise ValueError("Invalid task status.")
        tasks = tasks.filter(status=status)

    if priority:
        if priority not in valid_priorities:
            raise ValueError("Invalid task priority.")
        tasks = tasks.filter(priority=priority)

    return tasks


def get_overdue_tasks_for_project(project):
    today = timezone.localdate()

    return get_project_tasks(project).filter(
        deadline__lt=today
    ).exclude(status='completed')


def get_task_details(task_id):
    return Task.objects.select_related(
        'project',
        'created_by'
    ).prefetch_related(
        'assignments__project_member__group_member__user'
    ).get(id=task_id)
