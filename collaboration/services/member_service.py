
from django.db import transaction
from collaboration.models import Group, GroupMember


@transaction.atomic
def add_member(group, user):

    # Check if the group is closed
    if group.status == 'closed':
        raise ValueError("This group is closed.")

    # Check if the group is full
    if group.members.filter(status='active').count() >= group.max_members:
        raise ValueError("This group is full.")

    # Check if the user is already an active member
    existing_member = GroupMember.objects.filter(
        group=group,
        user=user,
        status='active'
    ).first()

    if existing_member:
        raise ValueError("This user is already a member.")

    # Add the user
    member = GroupMember.objects.create(
        group=group,
        user=user,
        role='member',
        status='active'
    )

    return member


@transaction.atomic
def remove_member(group, user, requester):

    # Find the member
    member = GroupMember.objects.filter(
        group=group,
        user=user,
        status='active'
    ).first()

    if not member:
        raise ValueError("This user is not an active member.")

    # Only the leader can remove another member
    requester_membership = GroupMember.objects.filter(
        group=group,
        user=requester,
        status='active',
        role='leader'
    ).first()

    if not requester_membership:
        raise ValueError("Only the group leader can remove members.")

    # The leader cannot remove themselves
    if user == requester:
        raise ValueError("The leader cannot remove themselves.")

    # Mark the member as having left
    member.status = 'left'
    member.save(update_fields=['status'])

    # Update group status if needed
    active_count = group.members.filter(status='active').count()

    if active_count < group.max_members and group.status == 'full':
        group.status = 'open'
        group.save(update_fields=['status'])

    return member

@transaction.atomic
def change_member_role(group, target_user, requester, new_role):

    if new_role not in ['leader', 'member']:
        raise ValueError("Invalid role.")

    # Check that the requester is the current leader
    current_leader = GroupMember.objects.filter(
        group=group,
        user=requester,
        status='active',
        role='leader'
    ).first()

    if not current_leader:
        raise ValueError("Only the current leader can change roles.")

    # Find the target member
    target_member = GroupMember.objects.filter(
        group=group,
        user=target_user,
        status='active'
    ).first()

    if not target_member:
        raise ValueError("This user is not an active member.")

    # No change needed
    if target_member.role == new_role:
        raise ValueError("This member already has this role.")

    # Transfer leadership
    if new_role == 'leader':
        current_leader.role = 'member'
        current_leader.save(update_fields=['role'])

        target_member.role = 'leader'
        target_member.save(update_fields=['role'])

    else:
        raise ValueError(
            "To transfer leadership, promote another member to leader."
        )

    return target_member
