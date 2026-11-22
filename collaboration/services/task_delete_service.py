
from django.db import transaction
from collaboration.models import GroupMember


@transaction.atomic
def delete_task(task, requester):
    project = task.project

    # Only the active group leader can delete tasks
    is_leader = GroupMember.objects.filter(
        group=project.group,
        user=requester,
        role='leader',
        status='active'
    ).exists()

    if not is_leader:
        raise ValueError("Only the group leader can delete tasks.")

    task.delete()

    return True
