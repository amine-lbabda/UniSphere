

from django.db import transaction
from django.utils import timezone

from collaboration.models import (
    TeamContract,
    ContractAcceptance,
    GroupMember
)


@transaction.atomic
def create_contract(group, requester, rules, objectives):

    # Only the group leader can create the contract
    leader = GroupMember.objects.filter(
        group=group,
        user=requester,
        role='leader',
        status='active'
    ).first()

    if not leader:
        raise ValueError("Only the group leader can create a contract.")

    # Check if a contract already exists
    if TeamContract.objects.filter(group=group).exists():
        raise ValueError("This group already has a contract.")

    # Create the contract
    contract = TeamContract.objects.create(
        group=group,
        rules=rules,
        objectives=objectives
    )

    # Create an acceptance record for every active member
    active_members = GroupMember.objects.filter(
        group=group,
        status='active'
    )

    for member in active_members:
        ContractAcceptance.objects.create(
            contract=contract,
            member=member
        )

    return contract


@transaction.atomic
def accept_contract(contract, user):

    # Find the user's active membership
    member = GroupMember.objects.filter(
        group=contract.group,
        user=user,
        status='active'
    ).first()

    if not member:
        raise ValueError("You are not an active member of this group.")

    # Find the acceptance record
    acceptance = ContractAcceptance.objects.filter(
        contract=contract,
        member=member
    ).first()

    if not acceptance:
        raise ValueError("No acceptance record found.")

    if acceptance.accepted:
        raise ValueError("You have already accepted this contract.")

    acceptance.accepted = True
    acceptance.accepted_at = timezone.now()
    acceptance.save()

    return acceptance

@transaction.atomic
def update_contract(contract, requester, rules, objectives):

    # Only the current group leader can update the contract
    leader = GroupMember.objects.filter(
        group=contract.group,
        user=requester,
        role='leader',
        status='active'
    ).first()

    if not leader:
        raise ValueError("Only the group leader can update the contract.")

    # Update contract information
    contract.rules = rules
    contract.objectives = objectives
    contract.save()

    # Get all active members
    active_members = GroupMember.objects.filter(
        group=contract.group,
        status='active'
    )

    # Reset acceptance for every active member
    for member in active_members:
        acceptance, created = ContractAcceptance.objects.get_or_create(
            contract=contract,
            member=member
        )

        acceptance.accepted = False
        acceptance.accepted_at = None
        acceptance.save()

    return contract

def is_contract_fully_accepted(contract):

    active_members = GroupMember.objects.filter(
        group=contract.group,
        status='active'
    )

    for member in active_members:
        acceptance = ContractAcceptance.objects.filter(
            contract=contract,
            member=member,
            accepted=True
        ).exists()

        if not acceptance:
            return False

    return True
