
from django.db import transaction

from collaboration.models import TaskAssignment, ProjectMember


@transaction.atomic
def assign_task(task, project_member, requester):

    project = task.project

    # Only the group leader can assign tasks
    is_leader = project.group.members.filter(
        user=requester,
        role='leader',
        status='active'
    ).exists()

    if not is_leader:
        raise ValueError("Only the group leader can assign tasks.")

    # The member must belong to this project
    if project_member.project_id != project.id:
        raise ValueError("This member does not belong to this project.")

    # The member must still be active in the group
    if project_member.group_member.status != 'active':
        raise ValueError("This member is not active.")

    # Prevent duplicate assignments
    if TaskAssignment.objects.filter(
        task=task,
        project_member=project_member
    ).exists():
        raise ValueError("This member is already assigned to this task.")

    return TaskAssignment.objects.create(
        task=task,
        project_member=project_member
    )


@transaction.atomic
def unassign_task(task, project_member, requester):

    is_leader = task.project.group.members.filter(
        user=requester,
        role='leader',
        status='active'
    ).exists()

    if not is_leader:
        raise ValueError("Only the group leader can unassign tasks.")

    assignment = TaskAssignment.objects.filter(
        task=task,
        project_member=project_member
    ).first()

    if not assignment:
        raise ValueError("This member is not assigned to this task.")

    assignment.delete()
