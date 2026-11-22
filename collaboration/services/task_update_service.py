
from django.db import transaction
from collaboration.models import GroupMember


@transaction.atomic
def update_task(
    task,
    requester,
    title=None,
    description=None,
    start_date=None,
    deadline=None,
    priority=None,
    estimated_hours=None
):
    project = task.project

    # Only the active group leader can edit task details
    is_leader = GroupMember.objects.filter(
        group=project.group,
        user=requester,
        role='leader',
        status='active'
    ).exists()

    if not is_leader:
        raise ValueError("Only the group leader can update task details.")

    if title is not None:
        if not title.strip():
            raise ValueError("Task title cannot be empty.")
        task.title = title.strip()

    if description is not None:
        task.description = description

    if start_date is not None:
        task.start_date = start_date

    if deadline is not None:
        task.deadline = deadline

    if priority is not None:
        valid_priorities = ['low', 'medium', 'high', 'urgent']

        if priority not in valid_priorities:
            raise ValueError("Invalid task priority.")

        task.priority = priority

    if estimated_hours is not None:
        if estimated_hours <= 0:
            raise ValueError("Estimated hours must be greater than zero.")
        task.estimated_hours = estimated_hours

    if task.deadline < task.start_date:
        raise ValueError("Task deadline cannot be before its start date.")

    if task.start_date < project.start_date:
        raise ValueError("Task cannot start before the project.")

    if task.deadline > project.deadline:
        raise ValueError("Task cannot end after the project deadline.")

    task.save()

    return task
