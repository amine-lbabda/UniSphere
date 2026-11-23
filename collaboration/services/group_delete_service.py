
from django.db import transaction
from collaboration.models import GroupMember


@transaction.atomic
def delete_group(group, requester):
    # Only the active group leader can delete the group
    is_leader = GroupMember.objects.filter(
        group=group,
        user=requester,
        role='leader',
        status='active'
    ).exists()

    if not is_leader:
        raise ValueError("Only the group leader can delete this group.")

    group.delete()

    return True
