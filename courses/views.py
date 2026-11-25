import json

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count, Q, Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import (
    ChoiceFormSet,
    CourseFilterForm,
    CourseForm,
    ProfileEditForm,
    QuestionForm,
    QuizForm,
    ResourceForm,
    StudentRegistrationForm,
)
from .models import (
    Category,
    Course,
    Enrollment,
    Notification,
    Question,
    Quiz,
    QuizAttempt,
    Resource,
    assign_modules_for_student,
    make_course_available_to_program,
    sync_program_enrollments,
)
from .programs import PROGRAM_DEFS, Filiere, dept_levels_by_category_id
from .roles import (
    get_profile,
    student_required,
    teacher_required,
    user_is_admin,
    user_is_student,
    user_is_teacher,
)
from . import admin_views  # noqa: F401 — registered via urls


def _unread_count(user):
    if user.is_authenticated:
        return Notification.objects.filter(recipient=user, is_read=False).count()
    return 0


def _student_program(user):
    """Parcours de l'étudiant (ex. 1A, 3IA) ou None."""
    if not user_is_student(user):
        return None
    profile = get_profile(user)
    return profile.academic_level if profile else None


def _published_for_student(user):
    """Modules publiés ET visibles pour le parcours de l'étudiant."""
    program = _student_program(user)
    qs = Course.objects.filter(status=Course.Status.PUBLISHED, is_visible=True)
    if program:
        qs = qs.filter(level=program)
    else:
        qs = qs.none()
    return qs


def _student_visible_resources(course, program):
    """Ressources accessibles à un étudiant du parcours donné (chapter order)."""
    resources = course.resources.select_related("chapter").order_by(
        "chapter__order", "order", "created_at"
    )
    return [
        r
        for r in resources
        if r.is_available_to_students
        and (r.target_level or course.level) == program
    ]


def _wants_json(request):
    return (
        request.headers.get("X-Requested-With") == "XMLHttpRequest"
        or "application/json" in (request.headers.get("Accept") or "")
    )


def _notify(recipient, title, message, level=Notification.Level.INFO, link="", course=None):
    return Notification.objects.create(
        recipient=recipient,
        title=title,
        message=message,
        level=level,
        link=link,
        course=course,
    )


def _notify_course_assigned(student, course):
    _notify(
        student,
        f"Nouveau module — {course.code}",
        f"« {course.title} » est disponible pour votre niveau ({course.get_level_display()}).",
        level=Notification.Level.INFO,
        link=course.get_absolute_url(),
        course=course,
    )


def _assign_course_to_class(course, *, notify=True):
    """Publie si besoin + inscrit tous les élèves du parcours cible."""
    return make_course_available_to_program(
        course,
        notify=notify,
        notify_callback=_notify_course_assigned if notify else None,
    )


def _module_progress(user, course, quizzes=None):
    """Progression étudiant : ressources + quiz réussis."""
    quizzes = list(quizzes if quizzes is not None else course.quizzes.filter(is_published=True))
    resource_count = course.resources.count()
    quiz_count = len(quizzes)
    passed = 0
    best_scores = {}
    if quizzes:
        attempts = QuizAttempt.objects.filter(
            student=user, quiz__in=quizzes
        ).order_by("-score")
        seen = set()
        for a in attempts:
            if a.quiz_id in seen:
                continue
            seen.add(a.quiz_id)
            best_scores[a.quiz_id] = a
            if a.passed:
                passed += 1
    # Pondération : présence ressources (40) + quiz (60)
    resource_part = 40 if resource_count else 20
    if quiz_count:
        quiz_part = int((passed / quiz_count) * 60)
    else:
        quiz_part = 60 if Enrollment.objects.filter(student=user, course=course).exists() else 0
    percent = min(100, resource_part + quiz_part) if Enrollment.objects.filter(
        student=user, course=course
    ).exists() else 0
    return {
        "percent": percent,
        "resource_count": resource_count,
        "quiz_count": quiz_count,
        "quizzes_passed": passed,
        "best_scores": best_scores,
        "label": (
            "Terminé" if percent >= 100 else
            "En cours" if percent > 0 else
            "À commencer"
        ),
    }


# ─── Front Office ───────────────────────────────────────────


def role_home(request):
    """Après connexion : redirige selon le rôle."""
    if not request.user.is_authenticated:
        return redirect("login")
    if user_is_admin(request.user):
        return redirect("courses:admin_dashboard")
    if user_is_teacher(request.user):
        return redirect("courses:back_dashboard")
    if user_is_student(request.user):
        return redirect("courses:student_dashboard")
    return redirect("courses:front_home")


def signup(request):
    """Création de compte étudiant avec choix filière + année/spécialité."""
    if request.user.is_authenticated:
        return redirect("courses:role_home")
    if request.method == "POST":
        form = StudentRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            assign_modules_for_student(user)
            login(request, user)
            messages.success(
                request,
                f"Bienvenue ! Parcours {user.profile.get_academic_level_display()} — "
                "vos modules ont été affectés.",
            )
            return redirect("courses:student_dashboard")
    else:
        form = StudentRegistrationForm()
    programs_by_filiere = {
        fil: [(c, lab) for c, lab, f, _ in PROGRAM_DEFS if f == fil]
        for fil in Filiere.LABELS
    }
    return render(
        request,
        "registration/signup.html",
        {
            "form": form,
            "programs_json": json.dumps(programs_by_filiere, ensure_ascii=False),
            "filiere_labels": Filiere.LABELS,
        },
    )


def _shell_layout(user):
    if user_is_admin(user):
        return "layouts/admin.html"
    if user_is_teacher(user):
        return "layouts/teacher.html"
    return "layouts/student.html"


@login_required
def profile_view(request):
    """Front Office — consulter mon profil."""
    profile = get_profile(request.user)
    return render(
        request,
        "courses/front/profile.html",
        {
            "profile": profile,
            "shell_layout": _shell_layout(request.user),
            "unread_notifications": _unread_count(request.user),
        },
    )


@login_required
def profile_edit(request):
    """Front Office — modifier mes informations personnelles."""
    profile = get_profile(request.user)
    initial = {
        "first_name": request.user.first_name,
        "last_name": request.user.last_name,
        "email": request.user.email,
        "phone": profile.phone,
        "student_id": profile.student_id,
    }
    if request.method == "POST":
        form = ProfileEditForm(
            request.POST, request.FILES, user=request.user
        )
        if form.is_valid():
            form.save()
            messages.success(request, "Profil mis à jour avec succès.")
            return redirect("courses:profile")
    else:
        form = ProfileEditForm(user=request.user, initial=initial)
    return render(
        request,
        "courses/front/profile_edit.html",
        {
            "form": form,
            "profile": profile,
            "shell_layout": _shell_layout(request.user),
            "unread_notifications": _unread_count(request.user),
        },
    )


def front_home(request):
    if user_is_student(request.user):
        published = _published_for_student(request.user)
        assign_modules_for_student(request.user)
    else:
        published = Course.objects.filter(status=Course.Status.PUBLISHED)
    featured_qs = published.select_related("category", "instructor")
    cat_filter = Q(courses__status=Course.Status.PUBLISHED)
    if user_is_student(request.user):
        cat_filter &= Q(courses__level=_student_program(request.user))
    context = {
        "featured": featured_qs[:6],
        "categories": Category.objects.annotate(
            course_count=Count("courses", filter=cat_filter)
        ),
        "stats": {
            "courses": published.count(),
            "resources": Resource.objects.filter(course__in=published).count(),
            "quizzes": Quiz.objects.filter(
                is_published=True, course__in=published
            ).count(),
            "categories": Category.objects.count(),
        },
    }
    return render(request, "courses/front/home.html", context)


def front_catalog(request):
    # Étudiant : UNIQUEMENT modules publiés de son parcours
    if user_is_student(request.user):
        assign_modules_for_student(request.user)
        courses = (
            _published_for_student(request.user)
            .select_related("category", "instructor")
            .annotate(res_count=Count("resources", distinct=True))
        )
        student_level = _student_program(request.user)
    else:
        courses = (
            Course.objects.filter(status=Course.Status.PUBLISHED, is_visible=True)
            .select_related("category", "instructor")
            .annotate(res_count=Count("resources", distinct=True))
        )
        student_level = None

    form = CourseFilterForm(request.GET or None)
    if form.is_valid():
        q = form.cleaned_data.get("q")
        category = form.cleaned_data.get("category")
        level = form.cleaned_data.get("level")
        if q:
            courses = courses.filter(
                Q(title__icontains=q)
                | Q(description__icontains=q)
                | Q(code__icontains=q)
                | Q(short_description__icontains=q)
            )
        if category:
            courses = courses.filter(category=category)
        # Les étudiants ne peuvent pas changer de parcours via le filtre
        if level and not user_is_student(request.user):
            courses = courses.filter(level=level)
    context = {
        "courses": courses,
        "form": form,
        "total": courses.count(),
        "student_level": student_level,
        "locked_to_level": user_is_student(request.user),
    }
    if user_is_student(request.user):
        # Cartes académiques avec progression réelle
        catalog_cards = []
        for course in courses:
            quizzes_c = list(course.quizzes.filter(is_published=True))
            prog = _module_progress(request.user, course, quizzes_c)
            catalog_cards.append(
                {
                    "course": course,
                    "progress": prog,
                    "res_count": getattr(course, "res_count", course.resources.count()),
                }
            )
        context["catalog_cards"] = catalog_cards
        return render(request, "courses/student/catalog.html", context)
    return render(request, "courses/front/catalog.html", context)


def front_detail(request, slug):
    course = get_object_or_404(
        Course.objects.select_related("category", "instructor").prefetch_related(
            "resources", "quizzes"
        ),
        slug=slug,
        status=Course.Status.PUBLISHED,
    )
    # Étudiant : publié + visible + parcours
    if user_is_student(request.user):
        if not course.is_visible:
            messages.error(request, "Ce module n’est pas accessible.")
            return redirect("courses:student_dashboard")
        program = _student_program(request.user)
        if course.level != program:
            messages.error(
                request,
                "Ce module n’est pas destiné à votre parcours.",
            )
            return redirect("courses:student_dashboard")
        assign_modules_for_student(request.user)

    related_qs = Course.objects.filter(
        status=Course.Status.PUBLISHED,
        is_visible=True,
        category=course.category,
    ).exclude(pk=course.pk)
    if user_is_student(request.user):
        related_qs = related_qs.filter(level=_student_program(request.user))
    related = related_qs[:3]

    # Ressources : parcours + is_visible pour étudiants
    if user_is_student(request.user):
        program = _student_program(request.user)
        visible_resources = _student_visible_resources(course, program)
    else:
        visible_resources = list(course.resources.all())

    published_quizzes = list(course.quizzes.filter(is_published=True))
    enrolled = False
    module_progress = None
    quiz_cards = []
    if request.user.is_authenticated and user_is_student(request.user):
        enrolled = Enrollment.objects.filter(
            student=request.user, course=course
        ).exists()
        attempts = QuizAttempt.objects.filter(
            student=request.user, quiz__course=course
        ).order_by("-completed_at")
        latest = {}
        for a in attempts:
            latest.setdefault(a.quiz_id, a)
        module_progress = _module_progress(request.user, course, published_quizzes)
        for q in published_quizzes:
            quiz_cards.append({"quiz": q, "attempt": latest.get(q.id)})
    else:
        quiz_cards = [{"quiz": q, "attempt": None} for q in published_quizzes]

    layout = (
        _role_layout(request.user)
        if request.user.is_authenticated
        else "base.html"
    )
    return render(
        request,
        "courses/front/detail.html",
        {
            "course": course,
            "related": related,
            "visible_resources": visible_resources,
            "published_quizzes": published_quizzes,
            "quiz_cards": quiz_cards,
            "enrolled": enrolled,
            "is_student_view": user_is_student(request.user),
            "module_progress": module_progress,
            "layout": layout,
        },
    )


@login_required
@student_required
@require_POST
def front_enroll(request, slug):
    """Inscription uniquement si le module publié cible le parcours de l'étudiant."""
    course = get_object_or_404(
        Course, slug=slug, status=Course.Status.PUBLISHED, is_visible=True
    )
    if course.level != _student_program(request.user):
        messages.error(
            request,
            "Ce module n’est pas destiné à votre parcours.",
        )
        return redirect("courses:student_dashboard")
    Enrollment.objects.get_or_create(student=request.user, course=course)
    _notify(
        request.user,
        f"Module affecté — {course.code}",
        f"Le module « {course.title} » est disponible dans votre espace.",
        level=Notification.Level.SUCCESS,
        link=course.get_absolute_url(),
        course=course,
    )
    messages.success(request, f"Module « {course.title} » ajouté à votre parcours.")
    return redirect("courses:front_detail", slug=slug)


@login_required
@student_required
def front_quiz_take(request, pk):
    quiz = get_object_or_404(
        Quiz.objects.select_related("course").prefetch_related(
            "questions__choices"
        ),
        pk=pk,
        is_published=True,
        course__status=Course.Status.PUBLISHED,
    )
    profile = get_profile(request.user)
    if quiz.course.level != profile.academic_level:
        messages.error(request, "Ce quiz ne correspond pas à votre niveau.")
        return redirect("courses:student_dashboard")
    if not Enrollment.objects.filter(student=request.user, course=quiz.course).exists():
        assign_modules_for_student(request.user)
    questions = list(quiz.questions.all())
    if request.method == "POST":
        total_points = 0
        earned = 0
        answers = {}
        for q in questions:
            total_points += q.points
            selected = request.POST.get(f"q_{q.pk}")
            answers[str(q.pk)] = selected
            if selected:
                choice = q.choices.filter(pk=selected, is_correct=True).first()
                if choice:
                    earned += q.points
        score = round((earned / total_points) * 100, 1) if total_points else 0
        passed = score >= quiz.passing_score
        attempt = QuizAttempt.objects.create(
            quiz=quiz,
            student=request.user,
            score=score,
            passed=passed,
            answers=answers,
        )
        _notify(
            request.user,
            f"Résultat quiz — {quiz.title}",
            f"Score : {score}% — {'Réussi' if passed else 'Non réussi'} (seuil {quiz.passing_score}%).",
            level=Notification.Level.SUCCESS if passed else Notification.Level.WARNING,
            link=f"/quiz/{quiz.pk}/resultat/{attempt.pk}/",
            course=quiz.course,
        )
        return redirect("courses:front_quiz_result", quiz_pk=quiz.pk, attempt_pk=attempt.pk)

    return render(
        request,
        "courses/front/quiz_take.html",
        {
            "quiz": quiz,
            "questions": questions,
            "layout": "layouts/student.html",
        },
    )


@login_required
@student_required
def front_quiz_result(request, quiz_pk, attempt_pk):
    attempt = get_object_or_404(
        QuizAttempt.objects.select_related("quiz", "quiz__course"),
        pk=attempt_pk,
        quiz_id=quiz_pk,
        student=request.user,
    )
    return render(
        request,
        "courses/front/quiz_result.html",
        {
            "attempt": attempt,
            "quiz": attempt.quiz,
            "layout": "layouts/student.html",
        },
    )


def _role_layout(user):
    if user_is_admin(user):
        return "layouts/admin.html"
    if user_is_teacher(user) and not user_is_student(user):
        return "layouts/teacher.html"
    if user_is_student(user):
        return "layouts/student.html"
    return "base.html"


@login_required
def front_notifications(request):
    notifs = Notification.objects.filter(recipient=request.user)
    return render(
        request,
        "courses/shared/notifications.html",
        {
            "notifications": notifs,
            "layout": _role_layout(request.user),
        },
    )


@login_required
@require_POST
def front_notification_read(request, pk):
    notif = get_object_or_404(Notification, pk=pk, recipient=request.user)
    notif.is_read = True
    notif.save(update_fields=["is_read"])
    if notif.link:
        return redirect(notif.link)
    return redirect("courses:front_notifications")


@login_required
@require_POST
def front_notifications_read_all(request):
    Notification.objects.filter(recipient=request.user, is_read=False).update(
        is_read=True
    )
    messages.success(request, "Toutes les notifications ont été marquées comme lues.")
    return redirect("courses:front_notifications")


# ─── Espace étudiant ────────────────────────────────────────


@login_required
@student_required
def student_dashboard(request):
    profile = get_profile(request.user)
    newly = assign_modules_for_student(request.user)
    for course in newly:
        _notify(
            request.user,
            f"Nouveau module — {course.code}",
            f"« {course.title} » a été affecté à votre niveau ({profile.get_academic_level_display()}).",
            level=Notification.Level.INFO,
            link=course.get_absolute_url(),
            course=course,
        )

    enrollments = (
        Enrollment.objects.filter(student=request.user)
        .select_related("course", "course__category", "course__instructor")
        .prefetch_related("course__resources", "course__quizzes")
        .order_by("course__code")
    )
    program = profile.academic_level
    my_courses = [
        e.course
        for e in enrollments
        if e.course.status == Course.Status.PUBLISHED
        and e.course.is_visible
        and e.course.level == program
    ]
    course_cards = []
    total_progress = 0
    progress_labels, progress_values = [], []
    for course in my_courses:
        quizzes_c = [q for q in course.quizzes.all() if q.is_published]
        prog = _module_progress(request.user, course, quizzes_c)
        total_progress += prog["percent"]
        course_cards.append({"course": course, "progress": prog})
        progress_labels.append(course.code)
        progress_values.append(prog["percent"])
    avg_progress = int(total_progress / len(course_cards)) if course_cards else 0

    quizzes = Quiz.objects.filter(
        is_published=True,
        course__in=my_courses,
    ).select_related("course")
    all_attempts = list(
        QuizAttempt.objects.filter(student=request.user)
        .select_related("quiz", "quiz__course")
        .order_by("completed_at")
    )
    attempts = list(reversed(all_attempts[-8:]))
    passed = sum(1 for a in all_attempts if a.passed)
    failed = sum(1 for a in all_attempts if not a.passed)
    score_labels = [a.completed_at.strftime("%d/%m") for a in all_attempts[-12:]]
    score_values = [a.score for a in all_attempts[-12:]]
    avg_score = (
        round(sum(a.score for a in all_attempts) / len(all_attempts), 1)
        if all_attempts else 0
    )
    upcoming = [
        q for q in quizzes
        if q.due_date and q.due_date >= timezone.now()
    ][:4]

    # Données desk / livre (réelles uniquement)
    library_resources = []
    for course in my_courses:
        for r in course.resources.all():
            if not r.is_available_to_students:
                continue
            target = r.target_level or course.level
            if target == program:
                library_resources.append({"resource": r, "course": course})
    library_resources = library_resources[:24]
    resource_total = sum(
        1
        for course in my_courses
        for r in course.resources.all()
        if r.is_available_to_students
        and (r.target_level or course.level) == program
    )
    recent_notifications = list(
        Notification.objects.filter(recipient=request.user).order_by("-created_at")[:5]
    )
    hour = timezone.localtime().hour
    if hour < 12:
        greeting = "Bonjour"
    elif hour < 18:
        greeting = "Bon après-midi"
    else:
        greeting = "Bonsoir"

    unread = Notification.objects.filter(
        recipient=request.user, is_read=False
    ).count()
    attention_count = len(upcoming) + unread
    if upcoming:
        contextual_message = (
            f"Votre prochain quiz approche : « {upcoming[0].title} »."
        )
    elif unread:
        contextual_message = (
            f"Vous avez {unread} alerte{'s' if unread > 1 else ''} à consulter."
        )
    elif attention_count == 0:
        contextual_message = "Vous êtes à jour pour aujourd’hui."
    else:
        contextual_message = (
            f"Vous avez {attention_count} élément"
            f"{'s' if attention_count > 1 else ''} qui mérite"
            f"{'' if attention_count > 1 else ''} attention."
        )

    # Today's Focus — premier quiz à échéance, sinon 1re alerte, sinon None
    focus = None
    if upcoming:
        q0 = upcoming[0]
        focus = {
            "kind": "quiz",
            "title": q0.title,
            "subtitle": (
                f"{q0.course.code} · échéance "
                f"{timezone.localtime(q0.due_date).strftime('%d/%m/%Y %H:%M')}"
            ),
            "url": reverse("courses:front_quiz_take", args=[q0.pk]),
            "percent": avg_progress,
            "cta": "Continuer →",
        }
    elif recent_notifications:
        n0 = recent_notifications[0]
        focus = {
            "kind": "alert",
            "title": n0.title,
            "subtitle": n0.message[:120],
            "url": n0.link or reverse("courses:front_notifications"),
            "percent": avg_progress,
            "cta": "Voir →",
        }

    # Academic journey — jalons réels uniquement
    journey = []
    for e in enrollments:
        if (
            e.course.status == Course.Status.PUBLISHED
            and e.course.is_visible
            and e.course.level == program
        ):
            journey.append(
                {
                    "label": e.course.code,
                    "detail": "Module affecté",
                    "when": e.enrolled_at,
                }
            )
    for a in all_attempts[-6:]:
        journey.append(
            {
                "label": a.quiz.title[:28],
                "detail": f"Quiz · {a.score}%",
                "when": a.completed_at,
            }
        )
    for q in upcoming:
        journey.append(
            {
                "label": q.title[:28],
                "detail": "Échéance",
                "when": q.due_date,
            }
        )
    journey.sort(key=lambda x: x["when"] or timezone.now())
    journey = journey[-8:]

    return render(
        request,
        "courses/student/dashboard.html",
        {
            "profile": profile,
            "my_courses": my_courses,
            "course_cards": course_cards,
            "avg_progress": avg_progress,
            "avg_score": avg_score,
            "quizzes": quizzes,
            "attempts": attempts,
            "upcoming": upcoming,
            "resource_total": resource_total,
            "library_resources": library_resources,
            "recent_notifications": recent_notifications,
            "greeting": greeting,
            "today": timezone.localtime().date(),
            "contextual_message": contextual_message,
            "attention_count": attention_count,
            "focus": focus,
            "journey": journey,
            "chart_progress": json.dumps(
                {"labels": progress_labels, "data": progress_values}
            ),
            "chart_scores": json.dumps(
                {"labels": score_labels, "data": score_values}
            ),
            "chart_pass": json.dumps(
                {"labels": ["Réussis", "Échoués"], "data": [passed, failed]}
            ),
        },
    )


@login_required
@student_required
def student_resources(request):
    """Bibliothèque numérique — ressources des modules affectés (données existantes)."""
    profile = get_profile(request.user)
    assign_modules_for_student(request.user)
    program = profile.academic_level
    enrollments = (
        Enrollment.objects.filter(student=request.user)
        .select_related("course")
        .prefetch_related("course__resources")
    )
    q = (request.GET.get("q") or "").strip()
    type_filter = (request.GET.get("type") or "").strip()
    items = []
    for e in enrollments:
        course = e.course
        if (
            course.status != Course.Status.PUBLISHED
            or not course.is_visible
            or course.level != program
        ):
            continue
        for r in course.resources.all():
            if not r.is_available_to_students:
                continue
            if (r.target_level or course.level) != program:
                continue
            if type_filter and r.resource_type != type_filter:
                continue
            if q and q.lower() not in r.title.lower() and q.lower() not in course.code.lower():
                continue
            items.append({"resource": r, "course": course})
    return render(
        request,
        "courses/student/resources.html",
        {
            "items": items,
            "q": q,
            "type_filter": type_filter,
            "type_choices": Resource.ResourceType.choices,
        },
    )


@login_required
@student_required
def student_quizzes(request):
    assign_modules_for_student(request.user)
    course_ids = Enrollment.objects.filter(student=request.user).values_list(
        "course_id", flat=True
    )
    quizzes = Quiz.objects.filter(
        is_published=True, course_id__in=course_ids
    ).select_related("course")
    latest = {}
    for a in QuizAttempt.objects.filter(student=request.user, quiz__in=quizzes).order_by(
        "-completed_at"
    ):
        latest.setdefault(a.quiz_id, a)
    cards = [{"quiz": q, "attempt": latest.get(q.id)} for q in quizzes]
    return render(request, "courses/student/quizzes.html", {"cards": cards})


@login_required
@student_required
def student_charts(request):
    """Dashboard Chart.js — stats réelles de l'étudiant."""
    from datetime import timedelta

    profile = get_profile(request.user)
    assign_modules_for_student(request.user)
    program = profile.academic_level
    enrollments = (
        Enrollment.objects.filter(student=request.user)
        .select_related("course", "course__category")
        .prefetch_related("course__resources", "course__quizzes")
        .order_by("course__code")
    )
    my_courses = [
        e.course
        for e in enrollments
        if e.course.status == Course.Status.PUBLISHED
        and e.course.is_visible
        and e.course.level == program
    ]

    progress_labels, progress_values = [], []
    total_progress = 0
    resource_total = 0
    for course in my_courses:
        quizzes_c = [q for q in course.quizzes.all() if q.is_published]
        prog = _module_progress(request.user, course, quizzes_c)
        progress_labels.append(course.code)
        progress_values.append(prog["percent"])
        total_progress += prog["percent"]
        resource_total += sum(
            1
            for r in course.resources.all()
            if r.is_available_to_students
            and (r.target_level or course.level) == program
        )
    avg_progress = int(total_progress / len(my_courses)) if my_courses else 0

    quizzes = Quiz.objects.filter(
        is_published=True, course__in=my_courses
    ).select_related("course")
    all_attempts = list(
        QuizAttempt.objects.filter(student=request.user)
        .select_related("quiz", "quiz__course")
        .order_by("completed_at")
    )
    passed = sum(1 for a in all_attempts if a.passed)
    failed = sum(1 for a in all_attempts if not a.passed)
    avg_score = (
        round(sum(a.score for a in all_attempts) / len(all_attempts), 1)
        if all_attempts
        else 0
    )
    score_labels = [a.completed_at.strftime("%d/%m") for a in all_attempts[-12:]]
    score_values = [a.score for a in all_attempts[-12:]]

    days, day_counts = [], []
    for i in range(13, -1, -1):
        day = timezone.localdate() - timedelta(days=i)
        days.append(day.strftime("%d/%m"))
        day_counts.append(
            sum(1 for a in all_attempts if a.completed_at.date() == day)
        )

    upcoming_count = sum(
        1 for q in quizzes if q.due_date and q.due_date >= timezone.now()
    )
    unread = Notification.objects.filter(
        recipient=request.user, is_read=False
    ).count()

    return render(
        request,
        "courses/student/charts.html",
        {
            "profile": profile,
            "module_count": len(my_courses),
            "resource_total": resource_total,
            "avg_progress": avg_progress,
            "quiz_count": quizzes.count(),
            "upcoming_count": upcoming_count,
            "attempt_count": len(all_attempts),
            "avg_score": avg_score,
            "unread": unread,
            "chart_progress": json.dumps(
                {"labels": progress_labels, "data": progress_values}
            ),
            "chart_scores": json.dumps(
                {"labels": score_labels, "data": score_values}
            ),
            "chart_pass": json.dumps(
                {"labels": ["Réussis", "Échoués"], "data": [passed, failed]}
            ),
            "chart_activity": json.dumps({"labels": days, "data": day_counts}),
        },
    )


@login_required
@student_required
def student_results(request):
    attempts = (
        QuizAttempt.objects.filter(student=request.user)
        .select_related("quiz", "quiz__course")
        .order_by("-completed_at")
    )
    return render(request, "courses/student/results.html", {"attempts": attempts})


# ─── Back Office (enseignants uniquement) ───────────────────


@login_required
@teacher_required
def back_dashboard(request):
    mine = Course.objects.filter(instructor=request.user).annotate(
        student_count=Count("enrollments", distinct=True),
        quiz_count=Count("quizzes", distinct=True),
        res_count=Count("resources", distinct=True),
    )
    quizzes = Quiz.objects.filter(course__instructor=request.user).annotate(
        q_count=Count("questions")
    )
    attempts_qs = QuizAttempt.objects.filter(quiz__course__instructor=request.user)
    recent_attempts = attempts_qs.select_related(
        "student", "quiz", "quiz__course"
    ).order_by("-completed_at")[:8]
    passed = attempts_qs.filter(passed=True).count()
    failed = attempts_qs.filter(passed=False).count()
    avg_score = attempts_qs.aggregate(a=Avg("score"))["a"] or 0

    from datetime import timedelta

    days, day_counts = [], []
    for i in range(13, -1, -1):
        day = timezone.localdate() - timedelta(days=i)
        days.append(day.strftime("%d/%m"))
        day_counts.append(attempts_qs.filter(completed_at__date=day).count())

    module_labels = [c.code for c in mine]
    module_students = [c.student_count for c in mine]
    status_data = [
        mine.filter(status=Course.Status.DRAFT).count(),
        mine.filter(status=Course.Status.PUBLISHED).count(),
        mine.filter(status=Course.Status.ARCHIVED).count(),
    ]

    my_resources = Resource.objects.filter(course__instructor=request.user)
    visible_courses = mine.filter(
        status=Course.Status.PUBLISHED, is_visible=True
    ).count()
    hidden_courses = mine.count() - visible_courses
    resources_hidden = my_resources.filter(is_visible=False).count()
    drafts = status_data[0]

    # Needs your attention — real DB signals only
    attention_items = []
    list_url = reverse("courses:back_course_list")
    if drafts:
        attention_items.append(
            {
                "icon": "📝",
                "tone": "warning",
                "title": (
                    f"{drafts} course{'s' if drafts != 1 else ''} still in draft"
                ),
                "detail": "Finish content, then publish when ready",
                "url": f"{list_url}?status=draft",
            }
        )
    if hidden_courses:
        attention_items.append(
            {
                "icon": "👁",
                "tone": "info",
                "title": (
                    f"{hidden_courses} course{'s' if hidden_courses != 1 else ''} "
                    "hidden from students"
                ),
                "detail": "Not student-accessible (draft, archived, or visibility off)",
                "url": f"{list_url}?visibility=hidden",
            }
        )
    if resources_hidden:
        attention_items.append(
            {
                "icon": "⚠️",
                "tone": "warning",
                "title": (
                    f"{resources_hidden} resource"
                    f"{'s' if resources_hidden != 1 else ''} still hidden"
                ),
                "detail": "Students cannot see these until you make them visible",
                "url": reverse("courses:back_resource_library") + "?visibility=hidden",
            }
        )
    week_end = timezone.now() + timedelta(days=7)
    scheduled_week = my_resources.filter(
        is_visible=True,
        scheduled_at__gt=timezone.now(),
        scheduled_at__lte=week_end,
    ).count()
    if scheduled_week:
        attention_items.append(
            {
                "icon": "📅",
                "tone": "info",
                "title": (
                    f"{scheduled_week} resource"
                    f"{'s' if scheduled_week != 1 else ''} scheduled this week"
                ),
                "detail": "Will become visible automatically at the set time",
                "url": reverse("courses:back_resource_library")
                + "?visibility=scheduled",
            }
        )
    empty_quizzes = list(quizzes.filter(q_count=0).select_related("course")[:5])
    for qz in empty_quizzes:
        attention_items.append(
            {
                "icon": "🧠",
                "tone": "danger",
                "title": f'Quiz “{qz.title}” has no questions',
                "detail": f"{qz.course.code} · add questions before publishing",
                "url": reverse("courses:back_quiz_detail", args=[qz.pk]),
            }
        )
    published_empty = mine.filter(
        status=Course.Status.PUBLISHED, is_visible=True, res_count=0
    )[:3]
    for c in published_empty:
        attention_items.append(
            {
                "icon": "📂",
                "tone": "info",
                "title": f'“{c.title}” is published with no resources',
                "detail": "Students see an empty course",
                "url": reverse("courses:back_course_detail", args=[c.pk]),
            }
        )

    # Activité récente réelle (cours + ressources + quiz)
    recent_activity = []
    for c in mine.order_by("-updated_at")[:8]:
        if c.created_at and (timezone.now() - c.created_at).days < 2:
            action = "created"
        elif c.status == Course.Status.PUBLISHED and c.is_visible:
            action = "published / visible"
        elif not c.is_visible:
            action = "hidden"
        else:
            action = "updated"
        recent_activity.append(
            {
                "kind": "course",
                "label": f"Course {c.code}",
                "detail": f"“{c.title}” — {action}",
                "when": c.updated_at,
                "url": reverse("courses:back_course_detail", args=[c.pk]),
            }
        )
    for r in my_resources.select_related("course").order_by("-created_at")[:6]:
        recent_activity.append(
            {
                "kind": "resource",
                "label": r.title,
                "detail": f"Resource · {r.course.code} · {r.visibility_label}",
                "when": r.created_at,
                "url": reverse("courses:back_course_detail", args=[r.course_id]),
            }
        )
    for qz in quizzes.select_related("course").order_by("-updated_at")[:4]:
        recent_activity.append(
            {
                "kind": "quiz",
                "label": qz.title,
                "detail": (
                    f"Quiz · {qz.course.code} · "
                    f"{'published' if qz.is_published else 'unpublished'}"
                ),
                "when": qz.updated_at,
                "url": reverse("courses:back_quiz_detail", args=[qz.pk]),
            }
        )
    recent_activity.sort(key=lambda x: x["when"], reverse=True)
    recent_activity = recent_activity[:10]

    hour = timezone.localtime().hour
    if hour < 12:
        greeting = "Good morning"
    elif hour < 18:
        greeting = "Good afternoon"
    else:
        greeting = "Good evening"
    professor_name = (
        request.user.get_full_name()
        or request.user.get_username()
        or "Professor"
    )
    if professor_name and " " in professor_name:
        # Prefer first name for greeting warmth
        professor_name = professor_name.split()[0]

    context = {
        "greeting": greeting,
        "professor_name": professor_name,
        "total_courses": mine.count(),
        "drafts": drafts,
        "published": status_data[1],
        "archived": status_data[2],
        "visible_courses": visible_courses,
        "hidden_courses": hidden_courses,
        "resources_count": my_resources.count(),
        "resources_visible": my_resources.filter(is_visible=True).count(),
        "resources_hidden": resources_hidden,
        "quizzes_count": quizzes.count(),
        "attempts_count": attempts_qs.count(),
        "students_count": Enrollment.objects.filter(
            course__instructor=request.user
        )
        .values("student")
        .distinct()
        .count(),
        "avg_score": round(avg_score, 1),
        "attention_items": attention_items,
        "recent_courses": mine.select_related("category")[:6],
        "recent_quizzes": quizzes.select_related("course")[:5],
        "recent_attempts": recent_attempts,
        "recent_activity": recent_activity,
        "chart_modules": json.dumps(
            {"labels": module_labels, "data": module_students}
        ),
        "chart_activity": json.dumps({"labels": days, "data": day_counts}),
        "chart_pass": json.dumps(
            {"labels": ["Passed", "Failed"], "data": [passed, failed]}
        ),
        "chart_status": json.dumps(
            {
                "labels": ["Draft", "Published", "Archived"],
                "data": status_data,
            }
        ),
        "chart_visibility": json.dumps(
            {
                "labels": ["Visible", "Hidden"],
                "data": [visible_courses, hidden_courses],
            }
        ),
    }
    return render(request, "courses/back/dashboard.html", context)


@login_required
@teacher_required
def back_quizzes(request):
    quizzes = (
        Quiz.objects.filter(course__instructor=request.user)
        .select_related("course")
        .annotate(
            attempt_count=Count("attempts", distinct=True),
            q_count=Count("questions", distinct=True),
            avg_score=Avg("attempts__score"),
            total_points=Sum("questions__points"),
        )
        .order_by("-updated_at")
    )
    q = (request.GET.get("q") or "").strip()
    status = (request.GET.get("status") or "").strip()
    course_id = (request.GET.get("course") or "").strip()
    if q:
        quizzes = quizzes.filter(
            Q(title__icontains=q)
            | Q(course__code__icontains=q)
            | Q(course__title__icontains=q)
        )
    if status == "published":
        quizzes = quizzes.filter(is_published=True)
    elif status == "draft":
        quizzes = quizzes.filter(is_published=False)
    elif status == "empty":
        quizzes = quizzes.filter(q_count=0)
    if course_id.isdigit():
        quizzes = quizzes.filter(course_id=int(course_id))

    quizzes = list(quizzes)
    all_mine = Quiz.objects.filter(course__instructor=request.user).annotate(
        q_count=Count("questions"),
        attempt_count=Count("attempts"),
    )
    stats = {
        "total": all_mine.count(),
        "published": all_mine.filter(is_published=True).count(),
        "draft": all_mine.filter(is_published=False).count(),
        "empty": all_mine.filter(q_count=0).count(),
        "attempts": QuizAttempt.objects.filter(
            quiz__course__instructor=request.user
        ).count(),
    }
    courses = Course.objects.filter(instructor=request.user).order_by("code")
    return render(
        request,
        "courses/back/quizzes.html",
        {
            "quizzes": quizzes,
            "stats": stats,
            "courses": courses,
            "q": q,
            "status": status,
            "course_id": course_id,
            "unread_notifications": _unread_count(request.user),
        },
    )


@login_required
@teacher_required
def back_quiz_create_standalone(request):
    """Créer un quiz en choisissant parmi ses modules."""
    my_courses = Course.objects.filter(instructor=request.user).order_by("code")
    if not my_courses.exists():
        messages.warning(request, "Créez d’abord un module avant d’ajouter un quiz.")
        return redirect("courses:back_course_create")
    if request.method == "POST":
        form = QuizForm(
            request.POST, include_course=True, course_queryset=my_courses
        )
        if form.is_valid():
            quiz = form.save(commit=False)
            quiz.course = form.cleaned_data["course"]
            quiz.save()
            if quiz.is_published:
                for enr in quiz.course.enrollments.select_related("student"):
                    _notify(
                        enr.student,
                        f"Nouveau quiz — {quiz.course.code}",
                        f"Le quiz « {quiz.title} » est disponible.",
                        level=Notification.Level.DEADLINE
                        if quiz.due_date
                        else Notification.Level.INFO,
                        link=f"/quiz/{quiz.pk}/",
                        course=quiz.course,
                    )
            messages.success(request, "Quiz créé. Ajoutez des questions.")
            return redirect("courses:back_quiz_detail", pk=quiz.pk)
    else:
        form = QuizForm(include_course=True, course_queryset=my_courses)
    return render(
        request,
        "courses/back/quiz_form.html",
        {
            "form": form,
            "course": None,
            "title": "Nouveau quiz",
            "select_course": True,
            "unread_notifications": _unread_count(request.user),
        },
    )


@login_required
@teacher_required
def back_students(request):
    enrollments = (
        Enrollment.objects.filter(course__instructor=request.user)
        .select_related("student", "student__profile", "course")
        .order_by("course__code", "student__username")
    )
    return render(request, "courses/back/students.html", {"enrollments": enrollments})


@login_required
@teacher_required
def back_course_list(request):
    courses = (
        Course.objects.filter(instructor=request.user)
        .select_related("category")
        .annotate(
            res_count=Count("resources", distinct=True),
            quiz_count=Count("quizzes", distinct=True),
            student_count=Count("enrollments", distinct=True),
        )
        .order_by("-updated_at")
    )
    form = CourseFilterForm(request.GET or None)
    if form.is_valid():
        q = form.cleaned_data.get("q")
        category = form.cleaned_data.get("category")
        level = form.cleaned_data.get("level")
        status = form.cleaned_data.get("status")
        if q:
            courses = courses.filter(
                Q(title__icontains=q) | Q(code__icontains=q) | Q(description__icontains=q)
            )
        if category:
            courses = courses.filter(category=category)
        if level:
            courses = courses.filter(level=level)
        if status:
            courses = courses.filter(status=status)
    # Filtre visibilité (GET visibility=visible|hidden)
    visibility = (request.GET.get("visibility") or "").strip()
    if visibility == "visible":
        courses = courses.filter(
            status=Course.Status.PUBLISHED, is_visible=True
        )
    elif visibility == "hidden":
        courses = courses.exclude(
            status=Course.Status.PUBLISHED, is_visible=True
        )

    # Needs Attention: courses that have at least one hidden resource
    resource_filter = (request.GET.get("resource") or "").strip()
    if resource_filter == "hidden":
        courses = courses.filter(resources__is_visible=False).distinct()

    courses = list(courses)
    stats = {
        "total": len(courses),
        "published": sum(1 for c in courses if c.status == Course.Status.PUBLISHED),
        "draft": sum(1 for c in courses if c.status == Course.Status.DRAFT),
        "archived": sum(1 for c in courses if c.status == Course.Status.ARCHIVED),
        "visible": sum(1 for c in courses if c.is_student_accessible),
        "hidden": sum(1 for c in courses if not c.is_student_accessible),
        "students": sum(c.student_count for c in courses),
        "resources": sum(c.res_count for c in courses),
        "quizzes": sum(c.quiz_count for c in courses),
    }
    return render(
        request,
        "courses/back/course_list.html",
        {
            "courses": courses,
            "form": form,
            "stats": stats,
            "visibility": visibility,
            "resource_filter": resource_filter,
            "status_choices": Course.Status.choices,
            "unread_notifications": _unread_count(request.user),
        },
    )


def _course_form_context(**extra):
    ctx = {
        "dept_levels_json": json.dumps(
            dept_levels_by_category_id(), ensure_ascii=False
        ),
    }
    ctx.update(extra)
    return ctx


@login_required
@teacher_required
def back_course_create(request):
    if request.method == "POST":
        form = CourseForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            course = form.save(commit=False)
            course.instructor = request.user
            if course.status == Course.Status.PUBLISHED and not course.published_at:
                course.published_at = timezone.now()
            course.save()
            newly = _assign_course_to_class(course, notify=True)
            if course.is_student_accessible:
                messages.success(
                    request,
                    f"Module « {course.title} » créé et affecté à {course.get_level_display()} "
                    f"({len(newly)} nouvel(le)s inscrit(e)s).",
                )
            else:
                messages.success(
                    request,
                    f"Module « {course.title} » créé. Publiez-le et rendez-le visible "
                    f"pour l’affecter aux étudiants de {course.get_level_display()}.",
                )
            return redirect("courses:back_course_detail", pk=course.pk)
    else:
        form = CourseForm(user=request.user)
    return render(
        request,
        "courses/back/course_form.html",
        _course_form_context(
            form=form,
            title="Nouveau module",
            mode="create",
            unread_notifications=_unread_count(request.user),
        ),
    )


@login_required
@teacher_required
def back_course_detail(request, pk):
    course = get_object_or_404(
        Course.objects.select_related("category", "instructor")
        .prefetch_related("resources", "quizzes", "enrollments__student")
        .annotate(
            res_count=Count("resources", distinct=True),
            quiz_count=Count("quizzes", distinct=True),
            student_count=Count("enrollments", distinct=True),
        ),
        pk=pk,
        instructor=request.user,
    )
    return render(
        request,
        "courses/back/course_detail.html",
        {
            "course": course,
            "status_choices": Course.Status.choices,
            "resource_type_choices": Resource.ResourceType.choices,
            "unread_notifications": _unread_count(request.user),
        },
    )


@login_required
@teacher_required
def back_course_edit(request, pk):
    course = get_object_or_404(Course, pk=pk, instructor=request.user)
    if request.method == "POST":
        form = CourseForm(
            request.POST, request.FILES, instance=course, user=request.user
        )
        if form.is_valid():
            course = form.save(commit=False)
            if course.status == Course.Status.PUBLISHED and not course.published_at:
                course.published_at = timezone.now()
            course.save()
            newly = _assign_course_to_class(course, notify=True)
            if newly:
                messages.success(
                    request,
                    f"Module mis à jour · {len(newly)} étudiant(s) de "
                    f"{course.get_level_display()} inscrit(s).",
                )
            else:
                messages.success(request, "Module mis à jour.")
            return redirect("courses:back_course_detail", pk=course.pk)
    else:
        form = CourseForm(instance=course, user=request.user)
    return render(
        request,
        "courses/back/course_form.html",
        _course_form_context(
            form=form,
            title=f"Modifier — {course.title}",
            mode="edit",
            course=course,
            unread_notifications=_unread_count(request.user),
        ),
    )


@login_required
@teacher_required
@require_POST
def back_course_delete(request, pk):
    course = get_object_or_404(Course, pk=pk, instructor=request.user)
    title = course.title
    course.delete()
    messages.success(request, f"Module « {title} » supprimé.")
    return redirect("courses:back_course_list")


@login_required
@teacher_required
@require_POST
def back_course_status(request, pk):
    course = get_object_or_404(Course, pk=pk, instructor=request.user)
    new_status = request.POST.get("status")
    if new_status in dict(Course.Status.choices):
        course.status = new_status
        if new_status == Course.Status.PUBLISHED and not course.published_at:
            course.published_at = timezone.now()
        course.save(update_fields=["status", "published_at", "updated_at"])
        newly = []
        if course.is_student_accessible:
            newly = sync_program_enrollments(
                course, notify=True, notify_callback=_notify_course_assigned
            )
        msg = f"Statut passé à « {course.get_status_display()} »."
        if newly:
            msg += f" {len(newly)} étudiant(s) de {course.get_level_display()} inscrit(s)."
        messages.success(request, msg)
    return redirect("courses:back_course_detail", pk=course.pk)


@login_required
@teacher_required
@require_POST
def back_course_toggle_visibility(request, pk):
    course = get_object_or_404(Course, pk=pk, instructor=request.user)
    if "is_visible" in request.POST:
        raw = str(request.POST.get("is_visible", "")).lower()
        course.is_visible = raw in ("1", "true", "on", "yes")
    else:
        course.is_visible = not course.is_visible
    course.save(update_fields=["is_visible", "updated_at"])
    newly = _assign_course_to_class(course, notify=True)

    payload = {
        "ok": True,
        "is_visible": course.is_visible,
        "student_accessible": course.is_student_accessible,
        "label": course.visibility_label,
        "status": course.status,
        "status_display": course.get_status_display(),
        "studio_state": course.studio_state,
        "studio_state_label": course.studio_state_label,
        "enrolled": len(newly),
        "message": (
            f"Course « {course.code} » is now "
            f"{'visible to students' if course.is_student_accessible else 'hidden from students'}"
            + (
                f" · {len(newly)} student(s) enrolled in {course.get_level_display()}."
                if newly
                else "."
            )
        ),
    }
    if _wants_json(request):
        return JsonResponse(payload)
    messages.success(request, payload["message"])
    next_url = request.POST.get("next") or reverse(
        "courses:back_course_detail", args=[course.pk]
    )
    return redirect(next_url)



def _preview_resource_groups(visible_resources):
    """Group student-visible resources by chapter for Preview as Student."""
    groups_map = {}
    unassigned = []
    for r in visible_resources:
        if r.chapter_id and r.chapter:
            bucket = groups_map.setdefault(
                r.chapter_id,
                {
                    "title": r.chapter.title,
                    "order": r.chapter.order,
                    "resources": [],
                },
            )
            bucket["resources"].append(r)
        else:
            unassigned.append(r)
    groups = sorted(groups_map.values(), key=lambda g: (g["order"], g["title"]))
    return groups, unassigned


def _preview_context(course, **extra):
    back = reverse("courses:back_course_detail", args=[course.pk])
    ctx = {
        "preview_back_url": back,
        "preview_edit_url": reverse("courses:back_course_edit", args=[course.pk]),
        "preview_builder_url": reverse(
            "courses:back_course_builder", args=[course.pk]
        ),
        "preview_course_url": reverse(
            "courses:back_course_preview", args=[course.pk]
        ),
        "preview_hint": (
            f"Digital Student Desk view for « {course.code} » — "
            "only student-visible content is shown."
        ),
        "unread_notifications": 0,
    }
    ctx.update(extra)
    return ctx


@login_required
@teacher_required
def back_course_preview(request, pk):
    """Preview as Student — same gates/filters students get, Studio chrome escape."""
    course = get_object_or_404(
        Course.objects.select_related("category", "instructor").prefetch_related(
            "resources__chapter", "quizzes", "chapters"
        ),
        pk=pk,
        instructor=request.user,
    )
    program = course.level
    preview_blocked = not course.is_student_accessible
    if preview_blocked:
        visible_resources = []
        published_quizzes = []
    else:
        visible_resources = _student_visible_resources(course, program)
        published_quizzes = list(
            course.quizzes.filter(is_published=True).order_by("order", "id")
        )
    resource_groups, unassigned_resources = _preview_resource_groups(
        visible_resources
    )
    quiz_cards = [{"quiz": q, "attempt": None} for q in published_quizzes]
    return render(
        request,
        "courses/front/detail.html",
        {
            **_preview_context(course),
            "course": course,
            "related": [],
            "visible_resources": visible_resources,
            "resource_groups": resource_groups,
            "unassigned_resources": unassigned_resources,
            "published_quizzes": published_quizzes,
            "quiz_cards": quiz_cards,
            "enrolled": True,
            "is_student_view": True,
            "is_preview": True,
            "preview_blocked": preview_blocked,
            "module_progress": None,
            "layout": "layouts/preview_student.html",
        },
    )


@login_required
@teacher_required
def back_resource_preview(request, pk):
    """Preview a single resource the way a student would encounter it."""
    resource = get_object_or_404(
        Resource.objects.select_related("course", "chapter", "course__category"),
        pk=pk,
        course__instructor=request.user,
    )
    course = resource.course
    student_sees = (
        course.is_student_accessible and resource.is_available_to_students
    )
    return render(
        request,
        "courses/back/resource_preview.html",
        {
            **_preview_context(
                course,
                preview_edit_url=reverse(
                    "courses:back_resource_edit", args=[resource.pk]
                ),
                preview_back_url=reverse("courses:back_resource_library"),
                preview_hint=(
                    f"Resource preview · « {resource.title} » — "
                    + (
                        "visible to students now."
                        if student_sees
                        else "currently hidden from students."
                    )
                ),
            ),
            "resource": resource,
            "course": course,
            "student_sees": student_sees,
            "layout": "layouts/preview_student.html",
        },
    )


@login_required
@teacher_required
def back_quiz_preview(request, pk):
    """Read-only quiz preview as a student would see the take screen."""
    quiz = get_object_or_404(
        Quiz.objects.select_related("course").prefetch_related(
            "questions__choices"
        ),
        pk=pk,
        course__instructor=request.user,
    )
    course = quiz.course
    questions = list(quiz.questions.all())
    student_sees = course.is_student_accessible and quiz.is_published
    return render(
        request,
        "courses/front/quiz_take.html",
        {
            **_preview_context(
                course,
                preview_edit_url=reverse(
                    "courses:back_quiz_detail", args=[quiz.pk]
                ),
                preview_back_url=reverse(
                    "courses:back_quiz_detail", args=[quiz.pk]
                ),
                preview_hint=(
                    f"Quiz preview · « {quiz.title} » — "
                    + (
                        "published for students."
                        if student_sees
                        else "not visible to students yet (unpublished or course hidden)."
                    )
                ),
            ),
            "quiz": quiz,
            "questions": questions,
            "is_preview": True,
            "student_sees": student_sees,
            "layout": "layouts/preview_student.html",
        },
    )


@login_required
@teacher_required
def back_resource_create(request, course_pk):
    course = get_object_or_404(Course, pk=course_pk, instructor=request.user)
    if request.method == "POST":
        form = ResourceForm(request.POST, request.FILES, course=course)
        if form.is_valid():
            resource = form.save(commit=False)
            resource.course = course
            if not resource.target_level:
                resource.target_level = course.level
            resource.save()
            # Notifier seulement si effectivement visible aux étudiants
            if resource.is_available_to_students:
                target = resource.target_level or course.level
                for enr in course.enrollments.select_related(
                    "student", "student__profile"
                ):
                    sp = getattr(enr.student, "profile", None)
                    if sp and sp.academic_level == target:
                        _notify(
                            enr.student,
                            f"Nouvelle ressource — {course.code}",
                            f"« {resource.title} » (niveau {resource.get_target_level_display()}).",
                            level=Notification.Level.INFO,
                            link=course.get_absolute_url(),
                            course=course,
                        )
            if _wants_json(request):
                return JsonResponse(
                    {
                        "ok": True,
                        "message": "Resource created successfully.",
                        "resource": {
                            "id": resource.pk,
                            "title": resource.title,
                            "type": resource.get_resource_type_display(),
                            "type_key": resource.resource_type,
                            "icon": resource.type_icon,
                            "order": resource.order,
                            "is_visible": resource.is_visible,
                            "visibility_label": resource.visibility_label,
                            "is_required": resource.is_required,
                            "target_level": resource.get_target_level_display(),
                            "edit_url": reverse(
                                "courses:back_resource_edit", args=[resource.pk]
                            ),
                            "toggle_url": reverse(
                                "courses:back_resource_toggle_visibility",
                                args=[resource.pk],
                            ),
                            "delete_url": reverse(
                                "courses:back_resource_delete", args=[resource.pk]
                            ),
                            "open_url": (
                                resource.url
                                or (resource.file.url if resource.file else "")
                            ),
                        },
                    }
                )
            messages.success(
                request,
                f"Resource « {resource.title} » created successfully.",
            )
            next_url = request.POST.get("next") or reverse(
                "courses:back_course_detail", args=[course.pk]
            )
            return redirect(next_url)
        if _wants_json(request):
            return JsonResponse(
                {"ok": False, "errors": form.errors}, status=400
            )
    else:
        form = ResourceForm(course=course)
    return render(
        request,
        "courses/back/resource_form.html",
        {
            "form": form,
            "course": course,
            "title": "Add resource",
            "mode": "create",
            "standalone": False,
            "unread_notifications": _unread_count(request.user),
        },
    )


@login_required
@teacher_required
@require_POST
def back_resource_toggle_visibility(request, pk):
    resource = get_object_or_404(
        Resource, pk=pk, course__instructor=request.user
    )
    if "is_visible" in request.POST:
        raw = str(request.POST.get("is_visible", "")).lower()
        resource.is_visible = raw in ("1", "true", "on", "yes")
    else:
        resource.is_visible = not resource.is_visible
    if resource.is_visible:
        resource.scheduled_at = None
    else:
        resource.scheduled_at = None
    resource.save(update_fields=["is_visible", "scheduled_at", "updated_at"])
    payload = {
        "ok": True,
        "is_visible": resource.is_visible,
        "student_accessible": resource.is_available_to_students,
        "label": resource.visibility_label,
        "studio_state": resource.studio_state,
        "studio_state_label": resource.studio_state_label,
        "message": (
            f"Resource « {resource.title} » is now "
            f"{'visible to students' if resource.is_available_to_students else 'hidden from students'}."
        ),
    }
    if _wants_json(request):
        return JsonResponse(payload)
    messages.success(request, payload["message"])
    return redirect("courses:back_course_detail", pk=resource.course_id)


@login_required
@teacher_required
def back_resource_edit(request, pk):
    resource = get_object_or_404(
        Resource, pk=pk, course__instructor=request.user
    )
    if request.method == "POST":
        form = ResourceForm(
            request.POST, request.FILES, instance=resource, course=resource.course
        )
        if form.is_valid():
            form.save()
            messages.success(request, "Resource updated successfully.")
            next_url = request.POST.get("next") or reverse(
                "courses:back_resource_library"
            )
            return redirect(next_url)
    else:
        form = ResourceForm(instance=resource, course=resource.course)
    return render(
        request,
        "courses/back/resource_form.html",
        {
            "form": form,
            "course": resource.course,
            "title": f"Edit — {resource.title}",
            "resource": resource,
            "mode": "edit",
            "standalone": False,
            "unread_notifications": _unread_count(request.user),
        },
    )

@login_required
@teacher_required
@require_POST
def back_resource_delete(request, pk):
    resource = get_object_or_404(
        Resource, pk=pk, course__instructor=request.user
    )
    course_pk = resource.course_id
    title = resource.title
    resource.delete()
    messages.success(request, f"Resource « {title} » deleted.")
    next_url = request.POST.get("next")
    if next_url:
        return redirect(next_url)
    return redirect("courses:back_course_detail", pk=course_pk)


# ─── Quiz back office ───────────────────────────────────────


@login_required
@teacher_required
def back_quiz_create(request, course_pk):
    course = get_object_or_404(Course, pk=course_pk, instructor=request.user)
    if request.method == "POST":
        form = QuizForm(request.POST)
        if form.is_valid():
            quiz = form.save(commit=False)
            quiz.course = course
            quiz.save()
            if quiz.is_published:
                for enr in course.enrollments.select_related("student"):
                    _notify(
                        enr.student,
                        f"Nouveau quiz — {course.code}",
                        f"Le quiz « {quiz.title} » est disponible.",
                        level=Notification.Level.DEADLINE
                        if quiz.due_date
                        else Notification.Level.INFO,
                        link=f"/quiz/{quiz.pk}/",
                        course=course,
                    )
            messages.success(request, "Quiz créé. Ajoutez des questions.")
            return redirect("courses:back_quiz_detail", pk=quiz.pk)
    else:
        form = QuizForm()
    return render(
        request,
        "courses/back/quiz_form.html",
        {
            "form": form,
            "course": course,
            "title": "Nouveau quiz",
            "unread_notifications": _unread_count(request.user),
        },
    )


@login_required
@teacher_required
def back_quiz_detail(request, pk):
    quiz = get_object_or_404(
        Quiz.objects.select_related("course").prefetch_related(
            "questions__choices"
        ),
        pk=pk,
        course__instructor=request.user,
    )
    attempts_qs = quiz.attempts.select_related("student")
    attempt_stats = attempts_qs.aggregate(
        attempt_count=Count("id"),
        avg_score=Avg("score"),
        passed_count=Count("id", filter=Q(passed=True)),
    )
    q_stats = quiz.questions.aggregate(
        q_count=Count("id"),
        total_points=Sum("points"),
    )
    quiz.q_count = q_stats["q_count"] or 0
    quiz.attempt_count = attempt_stats["attempt_count"] or 0
    avg = attempt_stats["avg_score"] or 0
    total_pts = q_stats["total_points"] or 0
    passed_count = attempt_stats["passed_count"] or 0
    avg_points = round((avg / 100.0) * total_pts, 1) if total_pts else None
    attempts = list(attempts_qs.order_by("-completed_at")[:50])
    return render(
        request,
        "courses/back/quiz_detail.html",
        {
            "quiz": quiz,
            "course": quiz.course,
            "attempts": attempts,
            "avg_score": round(avg, 1) if attempt_stats["avg_score"] is not None else None,
            "avg_points": avg_points,
            "total_points": total_pts,
            "pass_rate": (
                round((passed_count / quiz.attempt_count) * 100, 1)
                if quiz.attempt_count
                else None
            ),
            "unread_notifications": _unread_count(request.user),
        },
    )


@login_required
@teacher_required
@require_POST
def back_quiz_toggle_publish(request, pk):
    quiz = get_object_or_404(Quiz, pk=pk, course__instructor=request.user)
    if "is_published" in request.POST:
        raw = str(request.POST.get("is_published", "")).lower()
        quiz.is_published = raw in ("1", "true", "on", "yes")
    else:
        quiz.is_published = not quiz.is_published
    quiz.save(update_fields=["is_published", "updated_at"])
    if quiz.is_published:
        for enr in quiz.course.enrollments.select_related("student"):
            _notify(
                enr.student,
                f"Quiz published — {quiz.course.code}",
                f"« {quiz.title} » is now available.",
                level=Notification.Level.DEADLINE
                if quiz.due_date
                else Notification.Level.INFO,
                link=f"/quiz/{quiz.pk}/",
                course=quiz.course,
            )
    payload = {
        "ok": True,
        "is_published": quiz.is_published,
        "label": "Published" if quiz.is_published else "Draft",
        "message": (
            f"Quiz « {quiz.title} » is now "
            f"{'published' if quiz.is_published else 'unpublished'}."
        ),
    }
    if _wants_json(request):
        return JsonResponse(payload)
    messages.success(request, payload["message"])
    return redirect("courses:back_quiz_detail", pk=quiz.pk)


@login_required
@teacher_required
def back_quiz_edit(request, pk):
    quiz = get_object_or_404(Quiz, pk=pk, course__instructor=request.user)
    if request.method == "POST":
        form = QuizForm(request.POST, instance=quiz)
        if form.is_valid():
            form.save()
            messages.success(request, "Quiz mis à jour.")
            return redirect("courses:back_quiz_detail", pk=quiz.pk)
    else:
        form = QuizForm(instance=quiz)
    return render(
        request,
        "courses/back/quiz_form.html",
        {
            "form": form,
            "course": quiz.course,
            "quiz": quiz,
            "title": f"Modifier — {quiz.title}",
            "unread_notifications": _unread_count(request.user),
        },
    )


@login_required
@teacher_required
@require_POST
def back_quiz_delete(request, pk):
    quiz = get_object_or_404(Quiz, pk=pk, course__instructor=request.user)
    course_pk = quiz.course_id
    quiz.delete()
    messages.success(request, "Quiz supprimé.")
    next_url = request.POST.get("next") or request.GET.get("next")
    if next_url == "list":
        return redirect("courses:back_quizzes")
    return redirect("courses:back_course_detail", pk=course_pk)


@login_required
@teacher_required
def back_question_create(request, quiz_pk):
    quiz = get_object_or_404(Quiz, pk=quiz_pk, course__instructor=request.user)
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
            return redirect("courses:back_quiz_detail", pk=quiz.pk)
    else:
        form = QuestionForm()
        formset = ChoiceFormSet()
    return render(
        request,
        "courses/back/question_form.html",
        {
            "form": form,
            "formset": formset,
            "quiz": quiz,
            "title": "Nouvelle question",
            "unread_notifications": _unread_count(request.user),
        },
    )


@login_required
@teacher_required
@require_POST
def back_question_delete(request, pk):
    question = get_object_or_404(
        Question, pk=pk, quiz__course__instructor=request.user
    )
    quiz_pk = question.quiz_id
    question.delete()
    messages.success(request, "Question supprimée.")
    return redirect("courses:back_quiz_detail", pk=quiz_pk)
