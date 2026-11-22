
from django.db import transaction
from django.utils import timezone

from collaboration.models import (
    MeetingAttendance,
    GroupMember
)


@transaction.atomic
def initialize_meeting_attendance(meeting, requester):

    # Only the organizer can initialize attendance
    if meeting.organizer_id != requester.id:
        raise ValueError("Only the meeting organizer can initialize attendance.")

    # Get all active members of the project's group
    active_members = GroupMember.objects.filter(
        group=meeting.project.group,
        status='active'
    )

    # Create one pending attendance record per member
    for member in active_members:
        MeetingAttendance.objects.get_or_create(
            meeting=meeting,
            group_member=member
        )

    return MeetingAttendance.objects.filter(meeting=meeting)


@transaction.atomic
def respond_to_meeting(meeting, requester, response):

    if response not in ['accepted', 'declined']:
        raise ValueError("Response must be accepted or declined.")

    # Find the requester's active group membership
    membership = GroupMember.objects.filter(
        group=meeting.project.group,
        user=requester,
        status='active'
    ).first()

    if not membership:
        raise ValueError("You are not an active member of this group.")

    if meeting.status != 'scheduled':
        raise ValueError("You can only respond to scheduled meetings.")

    attendance = MeetingAttendance.objects.filter(
        meeting=meeting,
        group_member=membership
    ).first()

    if not attendance:
        raise ValueError("No attendance record exists for this meeting.")

    attendance.status = response
    attendance.responded_at = timezone.now()
    attendance.save(update_fields=['status', 'responded_at'])

    return attendance


def get_meeting_attendance(meeting):

    return MeetingAttendance.objects.filter(
        meeting=meeting
    ).select_related(
        'group_member__user'
    )
