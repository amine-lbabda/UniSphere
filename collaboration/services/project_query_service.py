
from collaboration.models import Project


def get_all_projects():
    return Project.objects.select_related(
        'group'
    ).order_by('-created_at')


def search_projects(keyword):
    projects = get_all_projects()

    if not keyword or not keyword.strip():
        return projects

    return projects.filter(
        title__icontains=keyword.strip()
    )


def filter_projects(status=None):
    projects = get_all_projects()

    if status:
        valid_statuses = [
            'planning',
            'in_progress',
            'completed',
            'cancelled'
        ]

        if status not in valid_statuses:
            raise ValueError("Invalid project status.")

        projects = projects.filter(status=status)

    return projects


def get_project_details(project_id):
    return Project.objects.select_related(
        'group'
    ).prefetch_related(
        'tasks',
        'members__group_member__user',
        'meetings'
    ).get(id=project_id)
