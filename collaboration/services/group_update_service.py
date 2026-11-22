
from django.db import transaction
from collaboration.models import GroupMember


@transaction.atomic
def update_group(
    group,
    requester,
    name=None,
    description=None,
    max_members=None
):
    # Only the active group leader can update the group
    is_leader = GroupMember.objects.filter(
        group=group,
        user=requester,
        role='leader',
        status='active'
    ).exists()

    if not is_leader:
        raise ValueError("Only the group leader can update this group.")

    if group.status == 'closed':
        raise ValueError("A closed group cannot be modified.")

    if name is not None:
        if not name.strip():
            raise ValueError("Group name cannot be empty.")
        group.name = name.strip()

    if description is not None:
        group.description = description

    if max_members is not None:
        if max_members < 1:
            raise ValueError("Maximum members must be at least 1.")

        active_count = group.members.filter(status='active').count()

        if max_members < active_count:
            raise ValueError(
                "Maximum members cannot be lower than the current number of active members."
            )

        group.max_members = max_members

        if active_count >= max_members:
            group.status = 'full'
        else:
            group.status = 'open'

    group.save()

    return group
