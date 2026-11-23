
from collaboration.models import Task
from collaboration.services.project_progress_service import calculate_project_progress
from collaboration.services.deadline_service import (
    get_overdue_tasks,
    get_upcoming_tasks
)
from collaboration.services.workload_service import get_member_workload


def get_project_dashboard(project):
    tasks = Task.objects.filter(project=project)

    total_tasks = tasks.count()
    completed_tasks = tasks.filter(status='completed').count()
    in_progress_tasks = tasks.filter(status='in_progress').count()
    todo_tasks = tasks.filter(status='todo').count()
    review_tasks = tasks.filter(status='review').count()

    overdue_tasks = get_overdue_tasks(project)
    upcoming_tasks = get_upcoming_tasks(project)

    workload = get_member_workload(project)

    return {
        'project': project,
        'progress': calculate_project_progress(project),

        'task_statistics': {
            'total': total_tasks,
            'completed': completed_tasks,
            'in_progress': in_progress_tasks,
            'todo': todo_tasks,
            'review': review_tasks,
        },

        'overdue_tasks': overdue_tasks,
        'overdue_count': overdue_tasks.count(),

        'upcoming_tasks': upcoming_tasks,
        'upcoming_count': upcoming_tasks.count(),

        'workload': workload,
    }
