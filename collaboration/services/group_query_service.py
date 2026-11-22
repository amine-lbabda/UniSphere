
from collaboration.models import Group


def get_all_groups():
    return Group.objects.all().order_by('-created_at')


def search_groups(keyword):
    if not keyword or not keyword.strip():
        return get_all_groups()

    return Group.objects.filter(
        name__icontains=keyword.strip()
    ).order_by('-created_at')


def filter_groups(status=None):
    groups = Group.objects.all()

    if status:
        valid_statuses = ['open', 'full', 'closed']

        if status not in valid_statuses:
            raise ValueError("Invalid group status.")

        groups = groups.filter(status=status)

    return groups.order_by('-created_at')


def get_group_details(group_id):
    return Group.objects.prefetch_related(
        'members__user',
        'invitations'
    ).get(id=group_id)
