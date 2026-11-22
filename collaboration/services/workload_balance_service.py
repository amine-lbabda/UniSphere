
from collaboration.services.workload_service import get_member_workload


def analyze_workload_balance(project):

    workload = get_member_workload(project)

    if not workload:
        return {
            'average_hours': 0,
            'members': []
        }

    # Calculate average assigned hours
    total_hours = sum(
        float(item['total_hours'])
        for item in workload
    )

    average_hours = total_hours / len(workload)

    results = []

    for item in workload:

        hours = float(item['total_hours'])

        if average_hours == 0:
            status = 'no_work'
        elif hours > average_hours * 1.5:
            status = 'overloaded'
        elif hours < average_hours * 0.5:
            status = 'underloaded'
        else:
            status = 'balanced'

        results.append({
            'member': item['member'],
            'role': item['role'],
            'total_hours': hours,
            'status': status
        })

    return {
        'average_hours': round(average_hours, 2),
        'members': results
    }
