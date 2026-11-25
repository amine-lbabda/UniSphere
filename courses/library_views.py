"""Academic Studio — Resource Library."""

from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import ResourceForm
from .models import Course, Resource
from .roles import teacher_required
from .views import _notify, _unread_count, _wants_json


@login_required
@teacher_required
def back_resource_library(request):
    resources = (
        Resource.objects.filter(course__instructor=request.user)
        .select_related("course", "course__instructor", "chapter")
        .order_by("-updated_at", "-created_at")
    )
    q = (request.GET.get("q") or "").strip()
    type_filter = (request.GET.get("type") or "").strip()
    vis = (request.GET.get("visibility") or "").strip()
    course_id = (request.GET.get("course") or "").strip()

    if q:
        resources = resources.filter(
            Q(title__icontains=q)
            | Q(description__icontains=q)
            | Q(course__code__icontains=q)
            | Q(course__title__icontains=q)
        )
    if type_filter and type_filter in dict(Resource.ResourceType.choices):
        resources = resources.filter(resource_type=type_filter)
    if course_id.isdigit():
        resources = resources.filter(course_id=int(course_id))

    resources = list(resources)
    if vis == "visible":
        resources = [r for r in resources if r.studio_state == "published"]
    elif vis == "hidden":
        resources = [r for r in resources if r.studio_state == "hidden"]
    elif vis == "scheduled":
        resources = [r for r in resources if r.studio_state == "scheduled"]
    elif vis == "draft":
        # Alias used by Needs Attention — hidden resources
        resources = [r for r in resources if r.studio_state == "hidden"]

    courses = Course.objects.filter(instructor=request.user).order_by("code")
    all_mine = list(
        Resource.objects.filter(course__instructor=request.user)
    )
    stats = {
        "total": len(all_mine),
        "visible": sum(1 for r in all_mine if r.studio_state == "published"),
        "hidden": sum(1 for r in all_mine if r.studio_state == "hidden"),
        "scheduled": sum(1 for r in all_mine if r.studio_state == "scheduled"),
    }

    return render(
        request,
        "courses/back/resource_library.html",
        {
            "resources": resources,
            "courses": courses,
            "q": q,
            "type_filter": type_filter,
            "visibility": vis,
            "course_id": course_id,
            "type_choices": Resource.ResourceType.choices,
            "stats": stats,
            "unread_notifications": _unread_count(request.user),
        },
    )


@login_required
@teacher_required
def back_resource_create_standalone(request):
    courses = Course.objects.filter(instructor=request.user).order_by("code")
    if not courses.exists():
        messages.warning(request, "Create a course before adding resources.")
        return redirect("courses:back_course_create")

    if request.method == "POST":
        form = ResourceForm(
            request.POST, request.FILES, include_course=True, user=request.user
        )
        if form.is_valid():
            resource = form.save(commit=False)
            resource.course = form.cleaned_data["course"]
            if not resource.target_level:
                resource.target_level = resource.course.level
            resource.save()
            if resource.is_available_to_students:
                _notify_resource(resource)
            messages.success(
                request,
                f"Resource « {resource.title} » created successfully.",
            )
            return redirect("courses:back_resource_library")
    else:
        initial_course = request.GET.get("course")
        course = None
        if initial_course and initial_course.isdigit():
            course = courses.filter(pk=int(initial_course)).first()
        form = ResourceForm(
            include_course=True, user=request.user, course=course
        )

    return render(
        request,
        "courses/back/resource_form.html",
        {
            "form": form,
            "course": getattr(form.fields.get("course"), "initial", None)
            and courses.filter(pk=form.fields["course"].initial).first(),
            "courses": courses,
            "title": "Add resource",
            "mode": "create",
            "standalone": True,
            "unread_notifications": _unread_count(request.user),
        },
    )


def _notify_resource(resource):
    course = resource.course
    target = resource.target_level or course.level
    for enr in course.enrollments.select_related("student", "student__profile"):
        sp = getattr(enr.student, "profile", None)
        if sp and sp.academic_level == target:
            _notify(
                enr.student,
                f"New resource — {course.code}",
                f"« {resource.title} » is now available.",
                level=Notification.Level.INFO,
                link=course.get_absolute_url(),
                course=course,
            )


@login_required
@teacher_required
@require_POST
def back_resource_set_visibility(request, pk):
    """Set visibility / schedule explicitly (Resource Library)."""
    resource = get_object_or_404(
        Resource, pk=pk, course__instructor=request.user
    )
    mode = (request.POST.get("mode") or "").strip()
    if mode == "visible":
        resource.is_visible = True
        resource.scheduled_at = None
    elif mode == "hidden":
        resource.is_visible = False
        resource.scheduled_at = None
    elif mode == "scheduled":
        raw = (request.POST.get("scheduled_at") or "").strip()
        resource.is_visible = True
        try:
            # HTML datetime-local
            resource.scheduled_at = timezone.datetime.fromisoformat(raw)
            if timezone.is_naive(resource.scheduled_at):
                resource.scheduled_at = timezone.make_aware(
                    resource.scheduled_at, timezone.get_current_timezone()
                )
        except ValueError:
            if _wants_json(request):
                return JsonResponse(
                    {"ok": False, "message": "Invalid schedule datetime."},
                    status=400,
                )
            messages.error(request, "Invalid schedule datetime.")
            return redirect("courses:back_resource_library")
    else:
        # toggle fallback
        resource.is_visible = not resource.is_visible
        if resource.is_visible:
            resource.scheduled_at = None

    resource.save(update_fields=["is_visible", "scheduled_at", "updated_at"])
    payload = {
        "ok": True,
        "is_visible": resource.is_visible,
        "student_accessible": resource.is_available_to_students,
        "label": resource.visibility_label,
        "studio_state": resource.studio_state,
        "studio_state_label": resource.studio_state_label,
        "scheduled_at": (
            resource.scheduled_at.isoformat() if resource.scheduled_at else None
        ),
        "message": (
            f"Resource « {resource.title} » — {resource.studio_state_label}."
        ),
    }
    if _wants_json(request):
        return JsonResponse(payload)
    messages.success(request, payload["message"])
    next_url = request.POST.get("next") or reverse("courses:back_resource_library")
    return redirect(next_url)
