
from collaboration.models import Task


def calculate_project_progress(project):

    total_tasks = Task.objects.filter(
        project=project
    ).count()

    if total_tasks == 0:
        return 0

    completed_tasks = Task.objects.filter(
        project=project,
        status='completed'
    ).count()

    progress = (completed_tasks / total_tasks) * 100

    return round(progress, 2)
