
from django.utils import timezone
from datetime import timedelta

from collaboration.models import Task


def get_overdue_tasks(project):
    """Return unfinished tasks whose deadlines have passed."""

    today = timezone.localdate()

    return Task.objects.filter(
        project=project,
        deadline__lt=today
    ).exclude(status='completed').order_by('deadline')


def get_upcoming_tasks(project, days=7):
    """Return unfinished tasks due within the next N days."""

    today = timezone.localdate()
    end_date = today + timedelta(days=days)

    return Task.objects.filter(
        project=project,
        deadline__gte=today,
        deadline__lte=end_date
    ).exclude(status='completed').order_by('deadline')


def get_completed_tasks(project):
    """Return completed tasks."""

    return Task.objects.filter(
        project=project,
        status='completed'
    ).order_by('-updated_at')
