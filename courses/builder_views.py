"""Academic Studio — Course Builder (chapters, structure, drag & drop order)."""

from __future__ import annotations

import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from .models import Course, CourseChapter, Quiz, Resource
from .roles import teacher_required
from .views import _unread_count, _wants_json


def _owned_course(request, pk):
    return get_object_or_404(Course, pk=pk, instructor=request.user)


def _owned_chapter(request, pk):
    return get_object_or_404(
        CourseChapter.objects.select_related("course"),
        pk=pk,
        course__instructor=request.user,
    )


def _item_payload(obj, itype):
    if itype == "resource":
        return {
            "type": "resource",
            "id": obj.pk,
            "title": obj.title,
            "icon": obj.type_icon,
            "meta": obj.get_resource_type_display(),
            "visible": obj.is_visible,
            "order": obj.order,
            "edit_url": reverse("courses:back_resource_edit", args=[obj.pk]),
        }
    return {
        "type": "quiz",
        "id": obj.pk,
        "title": obj.title,
        "icon": "🧠",
        "meta": "Quiz",
        "visible": obj.is_published,
        "order": obj.order,
        "edit_url": reverse("courses:back_quiz_detail", args=[obj.pk]),
    }


def _builder_structure(course):
    chapters = list(
        course.chapters.prefetch_related("resources", "quizzes").order_by("order", "id")
    )
    chapter_ids = {ch.pk for ch in chapters}
    structured = []
    for index, ch in enumerate(chapters, start=1):
        items = [
            _item_payload(r, "resource") for r in ch.resources.all()
        ] + [_item_payload(q, "quiz") for q in ch.quizzes.all()]
        items.sort(key=lambda it: (it.get("order", 0), it["id"]))
        structured.append(
            {
                "id": ch.pk,
                "title": ch.title,
                "order": ch.order,
                "index": index,
                "items": items,
            }
        )

    unassigned = [
        _item_payload(r, "resource")
        for r in course.resources.filter(chapter__isnull=True).order_by("order", "id")
    ] + [
        _item_payload(q, "quiz")
        for q in course.quizzes.filter(chapter__isnull=True).order_by("order", "id")
    ]
    unassigned.sort(key=lambda it: (it.get("order", 0), it["type"], it["id"]))
    return structured, unassigned, chapter_ids


@login_required
@teacher_required
def back_course_builder(request, pk):
    course = _owned_course(request, pk)
    chapters, unassigned, _ = _builder_structure(course)
    return render(
        request,
        "courses/back/course_builder.html",
        {
            "course": course,
            "chapters": chapters,
            "unassigned": unassigned,
            "chapters_json": json.dumps(chapters, ensure_ascii=False),
            "unassigned_json": json.dumps(unassigned, ensure_ascii=False),
            "unread_notifications": _unread_count(request.user),
        },
    )


@login_required
@teacher_required
@require_POST
def back_chapter_create(request, course_pk):
    course = _owned_course(request, course_pk)
    title = (request.POST.get("title") or "").strip() or f"Chapter {course.chapters.count() + 1}"
    next_order = (
        course.chapters.order_by("-order").values_list("order", flat=True).first() or 0
    ) + 1
    chapter = CourseChapter.objects.create(
        course=course, title=title[:200], order=next_order
    )
    payload = {
        "ok": True,
        "message": f"Chapter « {chapter.title} » added.",
        "chapter": {
            "id": chapter.pk,
            "title": chapter.title,
            "order": chapter.order,
            "items": [],
        },
    }
    if _wants_json(request):
        return JsonResponse(payload)
    messages.success(request, payload["message"])
    return redirect("courses:back_course_builder", pk=course.pk)


@login_required
@teacher_required
@require_POST
def back_chapter_rename(request, pk):
    chapter = _owned_chapter(request, pk)
    title = (request.POST.get("title") or "").strip()
    if not title:
        if _wants_json(request):
            return JsonResponse({"ok": False, "message": "Title required."}, status=400)
        messages.error(request, "Title required.")
        return redirect("courses:back_course_builder", pk=chapter.course_id)
    chapter.title = title[:200]
    chapter.save(update_fields=["title"])
    payload = {
        "ok": True,
        "message": "Chapter renamed.",
        "chapter": {"id": chapter.pk, "title": chapter.title},
    }
    if _wants_json(request):
        return JsonResponse(payload)
    messages.success(request, payload["message"])
    return redirect("courses:back_course_builder", pk=chapter.course_id)


@login_required
@teacher_required
@require_POST
def back_chapter_delete(request, pk):
    chapter = _owned_chapter(request, pk)
    course_id = chapter.course_id
    title = chapter.title
    Resource.objects.filter(chapter=chapter).update(chapter=None)
    Quiz.objects.filter(chapter=chapter).update(chapter=None)
    chapter.delete()
    payload = {
        "ok": True,
        "message": f"Chapter « {title} » removed. Items moved to Unassigned.",
    }
    if _wants_json(request):
        return JsonResponse(payload)
    messages.success(request, payload["message"])
    return redirect("courses:back_course_builder", pk=course_id)


@login_required
@teacher_required
@require_POST
def back_course_builder_reorder(request, pk):
    """Persist chapter order + item chapter assignment / order from Course Builder DnD."""
    course = _owned_course(request, pk)
    try:
        if request.content_type and "application/json" in request.content_type:
            data = json.loads(request.body.decode("utf-8") or "{}")
        else:
            data = json.loads(request.POST.get("payload") or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"ok": False, "message": "Invalid payload."}, status=400)

    chapters_payload = data.get("chapters") or []
    unassigned_payload = data.get("unassigned") or []

    owned_chapter_ids = set(
        course.chapters.values_list("id", flat=True)
    )
    owned_resource_ids = set(
        course.resources.values_list("id", flat=True)
    )
    owned_quiz_ids = set(course.quizzes.values_list("id", flat=True))

    seen_resources = set()
    seen_quizzes = set()

    def _validate_item(item):
        itype = item.get("type")
        iid = item.get("id")
        try:
            iid = int(iid)
        except (TypeError, ValueError):
            return None
        if itype == "resource" and iid in owned_resource_ids and iid not in seen_resources:
            seen_resources.add(iid)
            return ("resource", iid)
        if itype == "quiz" and iid in owned_quiz_ids and iid not in seen_quizzes:
            seen_quizzes.add(iid)
            return ("quiz", iid)
        return None

    with transaction.atomic():
        for ch_index, ch_data in enumerate(chapters_payload):
            try:
                ch_id = int(ch_data.get("id"))
            except (TypeError, ValueError):
                continue
            if ch_id not in owned_chapter_ids:
                continue
            CourseChapter.objects.filter(pk=ch_id, course=course).update(order=ch_index)
            for item_index, raw in enumerate(ch_data.get("items") or []):
                parsed = _validate_item(raw)
                if not parsed:
                    continue
                itype, iid = parsed
                if itype == "resource":
                    Resource.objects.filter(pk=iid, course=course).update(
                        chapter_id=ch_id, order=item_index
                    )
                else:
                    Quiz.objects.filter(pk=iid, course=course).update(
                        chapter_id=ch_id, order=item_index
                    )

        for item_index, raw in enumerate(unassigned_payload):
            parsed = _validate_item(raw)
            if not parsed:
                continue
            itype, iid = parsed
            if itype == "resource":
                Resource.objects.filter(pk=iid, course=course).update(
                    chapter=None, order=item_index
                )
            else:
                Quiz.objects.filter(pk=iid, course=course).update(
                    chapter=None, order=item_index
                )

        # Any owned items missing from payload stay where they are (safe)
        # but if payload is complete from UI, all appear. OK.

    chapters, unassigned, _ = _builder_structure(course)
    return JsonResponse(
        {
            "ok": True,
            "message": "Course structure saved.",
            "chapters": chapters,
            "unassigned": unassigned,
        }
    )
