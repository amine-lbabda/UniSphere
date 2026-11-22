
from django.db import transaction
from collaboration.models import TaskAssignment


@transaction.atomic
def update_task_status(task, requester, new_status):

    valid_statuses = [
        'todo',
        'in_progress',
        'review',
        'completed'
    ]

    if new_status not in valid_statuses:
        raise ValueError("Invalid task status.")

    # Only an assigned member or the group leader can update progress
    is_leader = task.project.group.members.filter(
        user=requester,
        role='leader',
        status='active'
    ).exists()

    is_assigned = TaskAssignment.objects.filter(
        task=task,
        project_member__group_member__user=requester,
        project_member__group_member__status='active'
    ).exists()

    if not is_leader and not is_assigned:
        raise ValueError(
            "You must be assigned to this task or be the group leader."
        )

    task.status = new_status
    task.save(update_fields=['status', 'updated_at'])

    return task
