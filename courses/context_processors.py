from .models import Notification
from .roles import get_profile, user_is_admin, user_is_student, user_is_teacher


def notifications(request):
    ctx = {
        "unread_notifications": 0,
        "is_teacher": False,
        "is_student": False,
        "is_admin": False,
        "user_profile": None,
    }
    if request.user.is_authenticated:
        ctx["unread_notifications"] = Notification.objects.filter(
            recipient=request.user, is_read=False
        ).count()
        ctx["is_admin"] = user_is_admin(request.user)
        ctx["is_teacher"] = user_is_teacher(request.user)
        ctx["is_student"] = user_is_student(request.user)
        ctx["user_profile"] = get_profile(request.user)
    return ctx
