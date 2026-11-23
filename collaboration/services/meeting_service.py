
from django.db import transaction
from collaboration.models import Meeting, GroupMember


@transaction.atomic
def create_meeting(
    project,
    requester,
    title,
    description,
    date,
    start_time,
    end_time,
    location="",
    meeting_link=""
):

    # Only active group members can organize meetings
    membership = GroupMember.objects.filter(
        group=project.group,
        user=requester,
        status='active'
    ).first()

    if not membership:
        raise ValueError(
            "Only active group members can organize meetings."
        )

    # Validate title
    if not title or not title.strip():
        raise ValueError("Meeting title cannot be empty.")

    # Validate meeting time
    if end_time <= start_time:
        raise ValueError(
            "Meeting end time must be after its start time."
        )

    # Validate meeting date
    from django.utils import timezone

    if date < timezone.localdate():
        raise ValueError("Meeting date cannot be in the past.")

    meeting = Meeting.objects.create(
        project=project,
        title=title.strip(),
        description=description,
        date=date,
        start_time=start_time,
        end_time=end_time,
        location=location,
        meeting_link=meeting_link,
        organizer=requester
    )

    return meeting
