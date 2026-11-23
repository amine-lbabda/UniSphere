from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect

from .models import UserProfile


def get_profile(user):
    if not user.is_authenticated:
        return None
    profile, _ = UserProfile.objects.get_or_create(
        user=user,
        defaults={
            "role": (
                UserProfile.Role.ADMIN
                if user.is_superuser
                else UserProfile.Role.STUDENT
            )
        },
    )
    if user.is_superuser and profile.role != UserProfile.Role.ADMIN:
        profile.role = UserProfile.Role.ADMIN
        profile.save(update_fields=["role"])
    return profile


def user_is_admin(user):
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    profile = get_profile(user)
    return bool(profile and profile.role == UserProfile.Role.ADMIN)


def user_is_teacher(user):
    if not user.is_authenticated:
        return False
    if user_is_admin(user):
        return True
    profile = get_profile(user)
    return bool(profile and profile.role == UserProfile.Role.TEACHER)


def user_is_student(user):
    if not user.is_authenticated:
        return False
    profile = get_profile(user)
    return bool(profile and profile.role == UserProfile.Role.STUDENT)


def teacher_required(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("login")
        if not user_is_teacher(request.user):
            messages.error(
                request,
                "Accès réservé aux enseignants.",
            )
            return redirect("courses:student_dashboard")
        return view_func(request, *args, **kwargs)

    return _wrapped


def student_required(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("login")
        if user_is_admin(request.user):
            return redirect("courses:admin_dashboard")
        if user_is_teacher(request.user) and not user_is_student(request.user):
            messages.info(request, "Redirection vers l’espace enseignant.")
            return redirect("courses:back_dashboard")
        if not user_is_student(request.user):
            messages.error(request, "Accès réservé aux étudiants.")
            return redirect("courses:front_home")
        return view_func(request, *args, **kwargs)

    return _wrapped


def admin_required(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("login")
        if not user_is_admin(request.user):
            messages.error(request, "Accès réservé à l’administrateur.")
            if user_is_teacher(request.user):
                return redirect("courses:back_dashboard")
            if user_is_student(request.user):
                return redirect("courses:student_dashboard")
            return redirect("courses:front_home")
        return view_func(request, *args, **kwargs)

    return _wrapped
