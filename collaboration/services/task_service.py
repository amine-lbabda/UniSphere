
from django.db import transaction
from collaboration.models import Task, ProjectMember, GroupMember


@transaction.atomic
def create_task(
    project,
    requester,
    title,
    description,
    start_date,
    deadline,
    priority='medium',
    estimated_hours=None
):
    # The requester must be an active member of the project group
    membership = GroupMember.objects.filter(
        group=project.group,
        user=requester,
        status='active'
    ).first()

    if not membership:
        raise ValueError("You must be an active group member to create tasks.")

    # Validate title
    if not title or not title.strip():
        raise ValueError("Task title cannot be empty.")

    # Validate dates
    if deadline < start_date:
        raise ValueError("Task deadline cannot be before its start date.")

    if start_date < project.start_date or deadline > project.deadline:
        raise ValueError("Task dates must be within the project dates.")

    # Validate priority
    valid_priorities = ['low', 'medium', 'high', 'urgent']
    if priority not in valid_priorities:
        raise ValueError("Invalid task priority.")

    if estimated_hours is not None and estimated_hours <= 0:
        raise ValueError("Estimated hours must be greater than zero.")

    return Task.objects.create(
        project=project,
        title=title.strip(),
        description=description,
        start_date=start_date,
        deadline=deadline,
        priority=priority,
        estimated_hours=estimated_hours,
        created_by=requester
    )
