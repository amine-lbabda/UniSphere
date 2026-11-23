
from django.db import transaction
from collaboration.models import GroupMember, Task


@transaction.atomic
def update_project(
    project,
    requester,
    title=None,
    description=None,
    start_date=None,
    deadline=None,
    status=None
):
    # Check group leader permissions
    is_leader = GroupMember.objects.filter(
        group=project.group,
        user=requester,
        role='leader',
        status='active'
    ).exists()

    if not is_leader:
        raise ValueError("Only the group leader can update this project.")

    if title is not None:
        if not title.strip():
            raise ValueError("Project title cannot be empty.")
        project.title = title.strip()

    if description is not None:
        project.description = description

    if start_date is not None:
        project.start_date = start_date

    if deadline is not None:
        project.deadline = deadline

    if status is not None:
        valid_statuses = [
            'planning',
            'in_progress',
            'completed',
            'cancelled'
        ]

        if status not in valid_statuses:
            raise ValueError("Invalid project status.")

        project.status = status

    if project.deadline < project.start_date:
        raise ValueError("Project deadline cannot be before its start date.")

    # Existing tasks must remain within the project dates
    tasks = Task.objects.filter(project=project)

    if tasks.filter(start_date__lt=project.start_date).exists():
        raise ValueError("Project start date cannot be after an existing task's start date.")

    if tasks.filter(deadline__gt=project.deadline).exists():
        raise ValueError("Project deadline cannot be before an existing task's deadline.")

    project.save()

    return project
