
from django.db import transaction
from collaboration.models import ContributionEvaluation, GroupMember


@transaction.atomic
def evaluate_member(
    project,
    project_member,
    requester,
    task_completion_score,
    work_quality_score,
    collaboration_score,
    deadline_respect_score,
    feedback=""
):
    # Only the group leader can evaluate members
    is_leader = GroupMember.objects.filter(
        group=project.group,
        user=requester,
        role='leader',
        status='active'
    ).exists()

    if not is_leader:
        raise ValueError("Only the group leader can evaluate members.")

    # Check that the member belongs to this project
    if project_member.project_id != project.id:
        raise ValueError("This member does not belong to this project.")

    if project_member.group_member.status != 'active':
        raise ValueError("Only active members can be evaluated.")

    # Validate scores
    scores = [
        task_completion_score,
        work_quality_score,
        collaboration_score,
        deadline_respect_score
    ]

    for score in scores:
        if not isinstance(score, int) or isinstance(score, bool) or not 0 <= score <= 5:
            raise ValueError("Every evaluation score must be an integer between 0 and 5.")

    evaluation, created = ContributionEvaluation.objects.update_or_create(
        project=project,
        project_member=project_member,
        defaults={
            'evaluated_by': requester,
            'task_completion_score': task_completion_score,
            'work_quality_score': work_quality_score,
            'collaboration_score': collaboration_score,
            'deadline_respect_score': deadline_respect_score,
            'feedback': feedback
        }
    )

    return evaluation


def get_project_evaluations(project):
    return ContributionEvaluation.objects.filter(
        project=project
    ).select_related(
        'project_member__group_member__user',
        'evaluated_by'
    )
