
from django.db.models import Sum, Count, Q

from collaboration.models import ProjectMember, TaskAssignment


def get_member_workload(project):

    project_members = ProjectMember.objects.filter(
        project=project,
        group_member__status='active'
    ).select_related(
        'group_member__user',
        'role'
    )

    workload = []

    for member in project_members:

        assignments = TaskAssignment.objects.filter(
            project_member=member
        ).exclude(
            task__status='completed'
        )

        statistics = assignments.aggregate(
            total_tasks=Count('id'),
            total_hours=Sum('task__estimated_hours')
        )

        workload.append({
            'member': member.group_member.user,
            'role': member.role.name,
            'total_tasks': statistics['total_tasks'],
            'total_hours': statistics['total_hours'] or 0
        })

    return workload
