
from django.db import transaction
from collaboration.models import GroupMember


@transaction.atomic
def delete_project(project, requester):
    # Only the active group leader can delete the project
    is_leader = GroupMember.objects.filter(
        group=project.group,
        user=requester,
        role='leader',
        status='active'
    ).exists()

    if not is_leader:
        raise ValueError("Only the group leader can delete this project.")

    project.delete()

    return True
