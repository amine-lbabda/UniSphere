"""Academic Studio — Course analytics from real database metrics only."""

from __future__ import annotations

import json
from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count
from django.shortcuts import get_object_or_404, render
from django.utils import timezone

from .models import Course, Enrollment, QuizAttempt
from .roles import teacher_required
from .views import _module_progress, _unread_count


@login_required
@teacher_required
def back_course_analytics(request, pk):
    course = get_object_or_404(
        Course.objects.select_related("category", "instructor").prefetch_related(
            "chapters", "resources", "quizzes"
        ),
        pk=pk,
        instructor=request.user,
    )

    enrollments = list(
        Enrollment.objects.filter(course=course).select_related(
            "student", "student__profile"
        )
    )
    student_count = len(enrollments)
    students = [e.student for e in enrollments]

    resources = list(course.resources.all())
    resources_total = len(resources)
    resources_available = sum(1 for r in resources if r.is_available_to_students)
    resources_hidden = sum(1 for r in resources if r.studio_state == "hidden")
    resources_scheduled = sum(1 for r in resources if r.studio_state == "scheduled")

    quizzes = list(course.quizzes.all())
    published_quizzes = [q for q in quizzes if q.is_published]
    attempts_qs = QuizAttempt.objects.filter(quiz__course=course)
    attempts_count = attempts_qs.count()
    avg_score = attempts_qs.aggregate(a=Avg("score"))["a"]
    avg_score = round(avg_score, 1) if avg_score is not None else None
    passed = attempts_qs.filter(passed=True).count()
    failed = attempts_qs.filter(passed=False).count()

    # Quiz participation: distinct students with ≥1 attempt / enrolled
    students_who_attempted = (
        attempts_qs.values("student").distinct().count() if student_count else 0
    )
    quiz_participation = (
        round((students_who_attempted / student_count) * 100, 1)
        if student_count
        else None
    )

    # Average progress across enrolled students (existing formula)
    progress_values = []
    student_rows = []
    for student in students:
        prog = _module_progress(student, course, published_quizzes)
        progress_values.append(prog["percent"])
        last_attempt = (
            attempts_qs.filter(student=student)
            .order_by("-completed_at")
            .first()
        )
        student_rows.append(
            {
                "name": student.get_full_name() or student.username,
                "progress": prog["percent"],
                "label": prog["label"],
                "quizzes_passed": prog["quizzes_passed"],
                "quiz_count": prog["quiz_count"],
                "last_activity": last_attempt.completed_at if last_attempt else None,
            }
        )
    student_rows.sort(key=lambda r: r["progress"], reverse=True)
    avg_progress = (
        int(round(sum(progress_values) / len(progress_values)))
        if progress_values
        else None
    )

    # Per-quiz metrics
    quiz_rows = []
    quiz_labels, quiz_avg_scores, quiz_attempts = [], [], []
    for q in quizzes:
        q_attempts = attempts_qs.filter(quiz=q)
        q_count = q_attempts.count()
        q_avg = q_attempts.aggregate(a=Avg("score"))["a"]
        distinct_students = q_attempts.values("student").distinct().count()
        participation = (
            round((distinct_students / student_count) * 100, 1)
            if student_count
            else None
        )
        quiz_rows.append(
            {
                "quiz": q,
                "questions": q.questions.count(),
                "attempts": q_count,
                "avg_score": round(q_avg, 1) if q_avg is not None else None,
                "participation": participation,
                "published": q.is_published,
            }
        )
        quiz_labels.append(q.title[:28] + ("…" if len(q.title) > 28 else ""))
        quiz_avg_scores.append(round(q_avg, 1) if q_avg is not None else 0)
        quiz_attempts.append(q_count)

    # Chapter content structure (resource availability — NOT view counts)
    def _availability_row(title, items):
        total = len(items)
        available = sum(1 for r in items if r.is_available_to_students)
        pct = int(round((available / total) * 100)) if total else 0
        return {
            "title": title,
            "total": total,
            "available": available,
            "percent": pct,
        }

    chapter_activity = []
    chapters = list(course.chapters.order_by("order", "id"))
    if chapters:
        for ch in chapters:
            chapter_activity.append(
                _availability_row(
                    ch.title, [r for r in resources if r.chapter_id == ch.pk]
                )
            )
        unassigned = [r for r in resources if not r.chapter_id]
        if unassigned:
            chapter_activity.append(_availability_row("Unassigned", unassigned))
    elif resources:
        chapter_activity.append(_availability_row("All resources", resources))

    # 14-day attempt activity
    days, day_counts = [], []
    for i in range(13, -1, -1):
        day = timezone.localdate() - timedelta(days=i)
        days.append(day.strftime("%d/%m"))
        day_counts.append(attempts_qs.filter(completed_at__date=day).count())

    # Score distribution buckets
    buckets = {"0–39": 0, "40–59": 0, "60–79": 0, "80–100": 0}
    for a in attempts_qs.only("score"):
        s = a.score or 0
        if s < 40:
            buckets["0–39"] += 1
        elif s < 60:
            buckets["40–59"] += 1
        elif s < 80:
            buckets["60–79"] += 1
        else:
            buckets["80–100"] += 1

    context = {
        "course": course,
        "student_count": student_count,
        "resources_total": resources_total,
        "resources_available": resources_available,
        "resources_hidden": resources_hidden,
        "resources_scheduled": resources_scheduled,
        "quizzes_total": len(quizzes),
        "quizzes_published": len(published_quizzes),
        "attempts_count": attempts_count,
        "avg_score": avg_score,
        "quiz_participation": quiz_participation,
        "avg_progress": avg_progress,
        "student_rows": student_rows[:20],
        "quiz_rows": quiz_rows,
        "chapter_activity": chapter_activity,
        "has_view_tracking": False,  # no ResourceView model — do not invent
        "chart_activity": json.dumps({"labels": days, "data": day_counts}),
        "chart_pass": json.dumps(
            {"labels": ["Passed", "Failed"], "data": [passed, failed]}
        ),
        "chart_quiz_scores": json.dumps(
            {"labels": quiz_labels, "data": quiz_avg_scores}
        ),
        "chart_quiz_attempts": json.dumps(
            {"labels": quiz_labels, "data": quiz_attempts}
        ),
        "chart_score_buckets": json.dumps(
            {"labels": list(buckets.keys()), "data": list(buckets.values())}
        ),
        "unread_notifications": _unread_count(request.user),
    }
    return render(request, "courses/back/course_analytics.html", context)
