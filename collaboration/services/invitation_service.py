
from django.db import transaction
from django.utils import timezone

from collaboration.models import GroupInvitation, GroupMember


@transaction.atomic
def send_invitation(group, invited_user, requester):
    # Only the active group leader can send invitations
    is_leader = GroupMember.objects.filter(
        group=group,
        user=requester,
        role='leader',
        status='active'
    ).exists()

    if not is_leader:
        raise ValueError("Only the group leader can send invitations.")

    if group.status == 'closed':
        raise ValueError("This group is closed.")

    active_count = GroupMember.objects.filter(
        group=group,
        status='active'
    ).count()

    if active_count >= group.max_members:
        raise ValueError("This group is full.")

    if GroupMember.objects.filter(
        group=group,
        user=invited_user,
        status='active'
    ).exists():
        raise ValueError("This user is already a group member.")

    existing = GroupInvitation.objects.filter(
        group=group,
        invited_user=invited_user,
        status='pending'
    ).first()

    if existing:
        raise ValueError("A pending invitation already exists.")

    return GroupInvitation.objects.create(
        group=group,
        invited_user=invited_user,
        invited_by=requester
    )


@transaction.atomic
def respond_to_invitation(invitation, requester, response):
    if invitation.invited_user_id != requester.id:
        raise ValueError("You cannot respond to someone else's invitation.")

    if invitation.status != 'pending':
        raise ValueError("This invitation has already been processed.")

    if response not in ['accepted', 'rejected']:
        raise ValueError("Invalid invitation response.")

    if response == 'accepted':
        if invitation.group.status == 'closed':
            raise ValueError("This group is closed.")

        active_count = GroupMember.objects.filter(
            group=invitation.group,
            status='active'
        ).count()

        if active_count >= invitation.group.max_members:
            raise ValueError("This group is full.")

        membership = GroupMember.objects.filter(
            group=invitation.group,
            user=requester
        ).first()

        if membership:
            if membership.status == 'active':
                raise ValueError("You are already a group member.")

            membership.status = 'active'
            membership.role = 'member'
            membership.save(update_fields=['status', 'role'])
        else:
            GroupMember.objects.create(
                group=invitation.group,
                user=requester,
                role='member',
                status='active'
            )

        # Update group status if it becomes full
        if active_count + 1 >= invitation.group.max_members:
            invitation.group.status = 'full'
            invitation.group.save(update_fields=['status'])

    invitation.status = response
    invitation.responded_at = timezone.now()
    invitation.save(update_fields=['status', 'responded_at'])

    return invitation


def get_user_invitations(user):
    return GroupInvitation.objects.filter(
        invited_user=user
    ).select_related(
        'group',
        'invited_by'
    ).order_by('-created_at')


def get_group_invitations(group):
    return GroupInvitation.objects.filter(
        group=group
    ).select_related(
        'invited_user',
        'invited_by'
    ).order_by('-created_at')
