import json
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import ChoiceFormSet, CourseForm, QuestionForm, QuizForm, ResourceForm
from .programs import dept_levels_by_category_id
from .models import (
    Category,
    Course,
    Enrollment,
    Notification,
    Question,
    Quiz,
    QuizAttempt,
    Resource,
    UserProfile,
)
from .programs import PROGRAM_GROUPS
from .roles import admin_required


def _chart(payload):
    return json.dumps(payload)


@login_required
@admin_required
def admin_dashboard(request):
    User = get_user_model()
    roles = {
        "students": UserProfile.objects.filter(role=UserProfile.Role.STUDENT).count(),
        "teachers": UserProfile.objects.filter(role=UserProfile.Role.TEACHER).count(),
        "admins": UserProfile.objects.filter(role=UserProfile.Role.ADMIN).count(),
    }
    status_counts = {
        s: Course.objects.filter(status=s).count()
        for s, _ in Course.Status.choices
    }
    level_counts = {
        label: Course.objects.filter(level=val, status=Course.Status.PUBLISHED).count()
        for val, label in Course._meta.get_field("level").choices
    }
    attempts = QuizAttempt.objects.all()
    passed = attempts.filter(passed=True).count()
    failed = attempts.filter(passed=False).count()
    avg_score = attempts.aggregate(a=Avg("score"))["a"] or 0

    # Last 14 days attempts
    days = []
    day_counts = []
    for i in range(13, -1, -1):
        day = timezone.localdate() - timedelta(days=i)
        days.append(day.strftime("%d/%m"))
        day_counts.append(
            QuizAttempt.objects.filter(completed_at__date=day).count()
        )

    cat_labels = []
    cat_values = []
    for cat in Category.objects.annotate(
        n=Count("courses", filter=Q(courses__status=Course.Status.PUBLISHED))
    ):
        cat_labels.append(cat.name)
        cat_values.append(cat.n)

    recent_users = User.objects.select_related("profile").order_by("-date_joined")[:6]
    recent_courses = Course.objects.select_related("instructor", "category")[:6]
    recent_attempts = QuizAttempt.objects.select_related(
        "student", "quiz", "quiz__course"
    )[:8]

    context = {
        "kpi": {
            "users": User.objects.count(),
            "courses": Course.objects.count(),
            "published": status_counts.get("published", 0),
            "quizzes": Quiz.objects.count(),
            "enrollments": Enrollment.objects.count(),
            "attempts": attempts.count(),
            "resources": Resource.objects.count(),
            "avg_score": round(avg_score, 1),
        },
        "chart_roles": _chart({
            "labels": ["Étudiants", "Enseignants", "Admins"],
            "data": [roles["students"], roles["teachers"], roles["admins"]],
        }),
        "chart_status": _chart({
            "labels": [l for _, l in Course.Status.choices],
            "data": [status_counts[s] for s, _ in Course.Status.choices],
        }),
        "chart_levels": _chart({
            "labels": list(level_counts.keys()),
            "data": list(level_counts.values()),
        }),
        "chart_pass": _chart({
            "labels": ["Réussis", "Échoués"],
            "data": [passed, failed],
        }),
        "chart_activity": _chart({"labels": days, "data": day_counts}),
        "chart_categories": _chart({"labels": cat_labels, "data": cat_values}),
        "recent_users": recent_users,
        "recent_courses": recent_courses,
        "recent_attempts": recent_attempts,
    }
    return render(request, "courses/admin/dashboard.html", context)


@login_required
@admin_required
def admin_users(request):
    User = get_user_model()
    users = User.objects.select_related("profile").order_by("-date_joined")
    return render(request, "courses/admin/users.html", {"users": users})


@login_required
@admin_required
def admin_user_edit(request, pk):
    User = get_user_model()
    user = get_object_or_404(User, pk=pk)
    profile, _ = UserProfile.objects.get_or_create(user=user)
    if request.method == "POST":
        profile.role = request.POST.get("role", profile.role)
        profile.academic_level = request.POST.get("academic_level", "") or ""
        profile.student_id = request.POST.get("student_id", "")
        profile.save()
        user.first_name = request.POST.get("first_name", user.first_name)
        user.last_name = request.POST.get("last_name", user.last_name)
        user.email = request.POST.get("email", user.email)
        user.is_active = request.POST.get("is_active") == "on"
        if profile.role == UserProfile.Role.ADMIN:
            user.is_staff = True
        user.save()
        messages.success(request, f"Profil de {user.username} mis à jour.")
        return redirect("courses:admin_users")
    return render(
        request,
        "courses/admin/user_form.html",
        {
            "edit_user": user,
            "profile": profile,
            "roles": UserProfile.Role.choices,
            "program_groups": PROGRAM_GROUPS,
        },
    )


@login_required
@admin_required
def admin_courses(request):
    courses = Course.objects.select_related("instructor", "category").annotate(
        student_count=Count("enrollments", distinct=True),
        quiz_count=Count("quizzes", distinct=True),
        res_count=Count("resources", distinct=True),
    )
    return render(request, "courses/admin/courses.html", {"courses": courses})


@login_required
@admin_required
def admin_course_create(request):
    if request.method == "POST":
        form = CourseForm(
            request.POST, request.FILES, user=request.user, include_instructor=True
        )
        if form.is_valid():
            course = form.save(commit=False)
            course.instructor = form.cleaned_data["instructor"]
            if course.status == Course.Status.PUBLISHED and not course.published_at:
                course.published_at = timezone.now()
            course.save()
            messages.success(request, f"Module « {course.title} » créé.")
            return redirect("courses:admin_courses")
    else:
        form = CourseForm(user=request.user, include_instructor=True)
    return render(
        request,
        "courses/admin/course_form.html",
        {
            "form": form,
            "title": "Nouveau module",
            "mode": "create",
            "dept_levels_json": json.dumps(
                dept_levels_by_category_id(), ensure_ascii=False
            ),
        },
    )


@login_required
@admin_required
def admin_course_edit(request, pk):
    course = get_object_or_404(Course, pk=pk)
    if request.method == "POST":
        form = CourseForm(
            request.POST,
            request.FILES,
            instance=course,
            user=request.user,
            include_instructor=True,
        )
        if form.is_valid():
            course = form.save(commit=False)
            course.instructor = form.cleaned_data["instructor"]
            if course.status == Course.Status.PUBLISHED and not course.published_at:
                course.published_at = timezone.now()
            course.save()
            messages.success(request, f"Module « {course.code} » mis à jour.")
            return redirect("courses:admin_courses")
    else:
        form = CourseForm(
            instance=course, user=request.user, include_instructor=True
        )
    return render(
        request,
        "courses/admin/course_form.html",
        {
            "form": form,
            "title": f"Modifier — {course.code}",
            "mode": "edit",
            "course": course,
            "dept_levels_json": json.dumps(
                dept_levels_by_category_id(), ensure_ascii=False
            ),
        },
    )


@login_required
@admin_required
@require_POST
def admin_course_delete(request, pk):
    course = get_object_or_404(Course, pk=pk)
    title = course.title
    course.delete()
    messages.success(request, f"Module « {title} » supprimé.")
    return redirect("courses:admin_courses")


@login_required
@admin_required
@require_POST
def admin_course_status(request, pk):
    course = get_object_or_404(Course, pk=pk)
    status = request.POST.get("status")
    if status in dict(Course.Status.choices):
        course.status = status
        if status == Course.Status.PUBLISHED and not course.published_at:
            course.published_at = timezone.now()
        course.save()
        messages.success(request, f"{course.code} → {course.get_status_display()}")
    return redirect("courses:admin_courses")


@login_required
@admin_required
def admin_resources(request):
    resources = Resource.objects.select_related(
        "course", "course__instructor"
    ).order_by("course__code", "order", "title")
    return render(
        request, "courses/admin/resources.html", {"resources": resources}
    )


@login_required
@admin_required
def admin_resource_create(request):
    if request.method == "POST":
        form = ResourceForm(request.POST, request.FILES, include_course=True)
        if form.is_valid():
            resource = form.save(commit=False)
            resource.course = form.cleaned_data["course"]
            if not resource.target_level:
                resource.target_level = resource.course.level
            resource.save()
            messages.success(request, f"Ressource « {resource.title} » créée.")
            return redirect("courses:admin_resources")
    else:
        form = ResourceForm(include_course=True)
    return render(
        request,
        "courses/admin/resource_form.html",
        {"form": form, "title": "Nouvelle ressource", "mode": "create"},
    )


@login_required
@admin_required
def admin_resource_edit(request, pk):
    resource = get_object_or_404(Resource.objects.select_related("course"), pk=pk)
    if request.method == "POST":
        form = ResourceForm(
            request.POST,
            request.FILES,
            instance=resource,
            course=resource.course,
            include_course=True,
        )
        if form.is_valid():
            resource = form.save(commit=False)
            resource.course = form.cleaned_data["course"]
            resource.save()
            messages.success(request, "Ressource mise à jour.")
            return redirect("courses:admin_resources")
    else:
        form = ResourceForm(
            instance=resource, course=resource.course, include_course=True
        )
    return render(
        request,
        "courses/admin/resource_form.html",
        {
            "form": form,
            "title": f"Modifier — {resource.title}",
            "mode": "edit",
            "resource": resource,
        },
    )


@login_required
@admin_required
@require_POST
def admin_resource_delete(request, pk):
    resource = get_object_or_404(Resource, pk=pk)
    title = resource.title
    resource.delete()
    messages.success(request, f"Ressource « {title} » supprimée.")
    return redirect("courses:admin_resources")


@login_required
@admin_required
def admin_quizzes(request):
    quizzes = Quiz.objects.select_related("course", "course__instructor").annotate(
        attempt_count=Count("attempts"),
        question_n=Count("questions"),
    )
    return render(request, "courses/admin/quizzes.html", {"quizzes": quizzes})


@login_required
@admin_required
def admin_quiz_create(request):
    if request.method == "POST":
        form = QuizForm(request.POST, include_course=True)
        if form.is_valid():
            quiz = form.save(commit=False)
            quiz.course = form.cleaned_data["course"]
            quiz.save()
            messages.success(request, "Quiz créé. Ajoutez des questions.")
            return redirect("courses:admin_quiz_detail", pk=quiz.pk)
    else:
        form = QuizForm(include_course=True)
    return render(
        request,
        "courses/admin/quiz_form.html",
        {"form": form, "title": "Nouveau quiz", "mode": "create"},
    )


@login_required
@admin_required
def admin_quiz_detail(request, pk):
    quiz = get_object_or_404(
        Quiz.objects.select_related("course", "course__instructor").prefetch_related(
            "questions__choices", "attempts__student"
        ),
        pk=pk,
    )
    return render(
        request,
        "courses/admin/quiz_detail.html",
        {"quiz": quiz, "course": quiz.course},
    )


@login_required
@admin_required
def admin_quiz_edit(request, pk):
    quiz = get_object_or_404(Quiz.objects.select_related("course"), pk=pk)
    if request.method == "POST":
        form = QuizForm(
            request.POST,
            instance=quiz,
            include_course=True,
            course=quiz.course,
        )
        if form.is_valid():
            quiz = form.save(commit=False)
            quiz.course = form.cleaned_data["course"]
            quiz.save()
            messages.success(request, "Quiz mis à jour.")
            return redirect("courses:admin_quiz_detail", pk=quiz.pk)
    else:
        form = QuizForm(instance=quiz, include_course=True, course=quiz.course)
    return render(
        request,
        "courses/admin/quiz_form.html",
        {
            "form": form,
            "title": f"Modifier — {quiz.title}",
            "mode": "edit",
            "quiz": quiz,
            "course": quiz.course,
        },
    )


@login_required
@admin_required
@require_POST
def admin_quiz_delete(request, pk):
    quiz = get_object_or_404(Quiz, pk=pk)
    title = quiz.title
    quiz.delete()
    messages.success(request, f"Quiz « {title} » supprimé.")
    return redirect("courses:admin_quizzes")


@login_required
@admin_required
def admin_question_create(request, quiz_pk):
    quiz = get_object_or_404(Quiz.objects.select_related("course"), pk=quiz_pk)
    if request.method == "POST":
        form = QuestionForm(request.POST)
        formset = ChoiceFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            question = form.save(commit=False)
            question.quiz = quiz
            question.save()
            formset.instance = question
            formset.save()
            if not question.choices.filter(is_correct=True).exists():
                messages.warning(
                    request,
                    "Question ajoutée, mais aucune réponse correcte n’est cochée.",
                )
            else:
                messages.success(request, "Question ajoutée.")
            return redirect("courses:admin_quiz_detail", pk=quiz.pk)
    else:
        form = QuestionForm()
        formset = ChoiceFormSet()
    return render(
        request,
        "courses/admin/question_form.html",
        {
            "form": form,
            "formset": formset,
            "quiz": quiz,
            "title": "Nouvelle question",
        },
    )


@login_required
@admin_required
@require_POST
def admin_question_delete(request, pk):
    question = get_object_or_404(Question, pk=pk)
    quiz_pk = question.quiz_id
    question.delete()
    messages.success(request, "Question supprimée.")
    return redirect("courses:admin_quiz_detail", pk=quiz_pk)


@login_required
@admin_required
def admin_enrollments(request):
    enrollments = Enrollment.objects.select_related(
        "student", "course", "course__instructor"
    ).order_by("-enrolled_at")
    return render(
        request, "courses/admin/enrollments.html", {"enrollments": enrollments}
    )


@login_required
@admin_required
@require_POST
def admin_enrollment_delete(request, pk):
    enr = get_object_or_404(Enrollment, pk=pk)
    enr.delete()
    messages.success(request, "Inscription supprimée.")
    return redirect("courses:admin_enrollments")


@login_required
@admin_required
def admin_categories(request):
    categories = Category.objects.annotate(course_count=Count("courses"))
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        color = request.POST.get("color", "#3b5bdb")
        if name:
            Category.objects.get_or_create(name=name, defaults={"color": color})
            messages.success(request, f"Département « {name} » ajouté.")
            return redirect("courses:admin_categories")
    return render(
        request, "courses/admin/categories.html", {"categories": categories}
    )


@login_required
@admin_required
def admin_notifications(request):
    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        message = request.POST.get("message", "").strip()
        audience = request.POST.get("audience", "all")
        level = request.POST.get("level", Notification.Level.INFO)
        users = get_user_model().objects.filter(is_active=True)
        if audience == "students":
            users = users.filter(profile__role=UserProfile.Role.STUDENT)
        elif audience == "teachers":
            users = users.filter(profile__role=UserProfile.Role.TEACHER)
        if title and message:
            bulk = [
                Notification(
                    recipient=u,
                    title=title,
                    message=message,
                    level=level,
                    link="/notifications/",
                )
                for u in users
            ]
            Notification.objects.bulk_create(bulk)
            messages.success(request, f"Alerte envoyée à {len(bulk)} utilisateur(s).")
            return redirect("courses:admin_notifications")
        messages.error(request, "Titre et message requis.")
    return render(
        request,
        "courses/admin/notifications.html",
        {"levels": Notification.Level.choices},
    )
