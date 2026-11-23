
from django.db import transaction
from collaboration.models import Decision, GroupMember


@transaction.atomic
def create_decision(
    meeting,
    requester,
    title,
    description="",
    responsible_member=None,
    deadline=None
):
    # Check that the requester is an active group member
    membership = GroupMember.objects.filter(
        group=meeting.project.group,
        user=requester,
        status='active'
    ).first()

    if not membership:
        raise ValueError("Only active group members can create decisions.")

    if not title or not title.strip():
        raise ValueError("Decision title cannot be empty.")

    # Check the responsible member, if provided
    if responsible_member is not None:
        if responsible_member.group_id != meeting.project.group_id:
            raise ValueError(
                "The responsible member must belong to this project group."
            )

        if responsible_member.status != 'active':
            raise ValueError("The responsible member must be active.")

    if deadline is not None and deadline < meeting.date:
        raise ValueError("The deadline cannot be before the meeting date.")

    return Decision.objects.create(
        meeting=meeting,
        title=title.strip(),
        description=description,
        responsible_member=responsible_member,
        deadline=deadline,
        created_by=requester
    )


@transaction.atomic
def update_decision_status(decision, requester, new_status):
    valid_statuses = ['pending', 'in_progress', 'completed']

    if new_status not in valid_statuses:
        raise ValueError("Invalid decision status.")

    is_leader = decision.meeting.project.group.members.filter(
        user=requester,
        role='leader',
        status='active'
    ).exists()

    is_responsible = (
        decision.responsible_member is not None
        and decision.responsible_member.user_id == requester.id
        and decision.responsible_member.status == 'active'
    )

    if not is_leader and not is_responsible:
        raise ValueError(
            "Only the group leader or responsible member can update this decision."
        )

    decision.status = new_status
    decision.save(update_fields=['status', 'updated_at'])

    return decision


def get_meeting_decisions(meeting):
    return Decision.objects.filter(
        meeting=meeting
    ).select_related(
        'responsible_member__user',
        'created_by'
    ).order_by('-created_at')
