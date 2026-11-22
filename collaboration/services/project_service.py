
from django.db import transaction
from collaboration.models import Project, GroupMember


@transaction.atomic
def create_project(group, requester, title, description, start_date, deadline):

    # Only the active group leader can create a project
    leader = GroupMember.objects.filter(
        group=group,
        user=requester,
        role='leader',
        status='active'
    ).first()

    if not leader:
        raise ValueError("Only the group leader can create a project.")

    # One project per group
    if Project.objects.filter(group=group).exists():
        raise ValueError("This group already has a project.")

    if deadline < start_date:
        raise ValueError("The deadline cannot be before the start date.")

    if not title.strip():
        raise ValueError("Project title cannot be empty.")

    project = Project.objects.create(
        group=group,
        title=title,
        description=description,
        start_date=start_date,
        deadline=deadline,
        status='planning'
    )

    return project
