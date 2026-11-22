
from django.db import transaction

from collaboration.models import MeetingMinutes, GroupMember


@transaction.atomic
def create_meeting_minutes(
    meeting,
    requester,
    discussion_summary,
    decisions="",
    action_items=""
):

    # Only active group members can record minutes
    membership = GroupMember.objects.filter(
        group=meeting.project.group,
        user=requester,
        status='active'
    ).first()

    if not membership:
        raise ValueError("Only active group members can record minutes.")

    if not discussion_summary or not discussion_summary.strip():
        raise ValueError("Discussion summary cannot be empty.")

    # One set of minutes per meeting
    if MeetingMinutes.objects.filter(meeting=meeting).exists():
        raise ValueError("Meeting minutes already exist.")

    return MeetingMinutes.objects.create(
        meeting=meeting,
        discussion_summary=discussion_summary.strip(),
        decisions=decisions,
        action_items=action_items,
        created_by=requester
    )


@transaction.atomic
def update_meeting_minutes(
    minutes,
    requester,
    discussion_summary,
    decisions="",
    action_items=""
):

    # Only the person who created the minutes or the group leader
    # can update them.
    is_creator = minutes.created_by_id == requester.id

    is_leader = minutes.meeting.project.group.members.filter(
        user=requester,
        role='leader',
        status='active'
    ).exists()

    if not is_creator and not is_leader:
        raise ValueError("You are not allowed to update these minutes.")

    if not discussion_summary or not discussion_summary.strip():
        raise ValueError("Discussion summary cannot be empty.")

    minutes.discussion_summary = discussion_summary.strip()
    minutes.decisions = decisions
    minutes.action_items = action_items

    minutes.save()

    return minutes
