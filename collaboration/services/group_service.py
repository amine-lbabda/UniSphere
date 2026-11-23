
from django.db import transaction
from collaboration.models import Group, GroupMember


@transaction.atomic
def create_group(name, description, creator, max_members=5):

    group = Group.objects.create(
        name=name,
        description=description,
        created_by=creator,
        max_members=max_members
    )

    GroupMember.objects.create(
        group=group,
        user=creator,
        role='leader',
        status='active'
    )

    return group
