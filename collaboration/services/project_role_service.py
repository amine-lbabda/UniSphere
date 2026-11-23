
from django.db import transaction
from collaboration.models import ProjectRole, ProjectMember, GroupMember


@transaction.atomic
def create_project_role(project, requester, name, description=""):

    # Only the group leader can manage project roles
    leader = GroupMember.objects.filter(
        group=project.group,
        user=requester,
        role='leader',
        status='active'
    ).first()

    if not leader:
        raise ValueError("Only the group leader can create project roles.")

    if not name.strip():
        raise ValueError("Role name cannot be empty.")

    if ProjectRole.objects.filter(
        project=project,
        name__iexact=name
    ).exists():
        raise ValueError("This role already exists in the project.")

    return ProjectRole.objects.create(
        project=project,
        name=name.strip(),
        description=description
    )


@transaction.atomic
def assign_project_role(project, group_member, role, requester):

    # Only the group leader can assign roles
    leader = GroupMember.objects.filter(
        group=project.group,
        user=requester,
        role='leader',
        status='active'
    ).first()

    if not leader:
        raise ValueError("Only the group leader can assign project roles.")

    # The member must belong to this project's group
    if group_member.group_id != project.group_id:
        raise ValueError("This member does not belong to the project group.")

    if group_member.status != 'active':
        raise ValueError("Only active group members can receive project roles.")

    # The role must belong to this project
    if role.project_id != project.id:
        raise ValueError("This role does not belong to this project.")

    assignment, created = ProjectMember.objects.update_or_create(
        project=project,
        group_member=group_member,
        defaults={'role': role}
    )

    return assignment


def all_members_have_roles(project):

    active_members = GroupMember.objects.filter(
        group=project.group,
        status='active'
    )

    for member in active_members:
        if not ProjectMember.objects.filter(
            project=project,
            group_member=member
        ).exists():
            return False

    return True
