from django.urls import path

from . import admin_views, views

app_name = "courses"

urlpatterns = [
    # Public
    path("", views.front_home, name="front_home"),
    path("inscription/", views.signup, name="signup"),
    path("espace/", views.role_home, name="role_home"),
    path("catalogue/", views.front_catalog, name="front_catalog"),
    path("modules/<slug:slug>/", views.front_detail, name="front_detail"),
    path("modules/<slug:slug>/inscription/", views.front_enroll, name="front_enroll"),
    path("quiz/<int:pk>/", views.front_quiz_take, name="front_quiz_take"),
    path(
        "quiz/<int:quiz_pk>/resultat/<int:attempt_pk>/",
        views.front_quiz_result,
        name="front_quiz_result",
    ),
    path("notifications/", views.front_notifications, name="front_notifications"),
    path(
        "notifications/<int:pk>/lire/",
        views.front_notification_read,
        name="front_notification_read",
    ),
    path(
        "notifications/tout-lire/",
        views.front_notifications_read_all,
        name="front_notifications_read_all",
    ),
    # Étudiant
    path("etudiant/", views.student_dashboard, name="student_dashboard"),
    path("etudiant/quiz/", views.student_quizzes, name="student_quizzes"),
    path("etudiant/resultats/", views.student_results, name="student_results"),
    # Enseignant
    path("back/", views.back_dashboard, name="back_dashboard"),
    path("back/modules/", views.back_course_list, name="back_course_list"),
    path("back/modules/nouveau/", views.back_course_create, name="back_course_create"),
    path("back/modules/<int:pk>/", views.back_course_detail, name="back_course_detail"),
    path(
        "back/modules/<int:pk>/modifier/",
        views.back_course_edit,
        name="back_course_edit",
    ),
    path(
        "back/modules/<int:pk>/supprimer/",
        views.back_course_delete,
        name="back_course_delete",
    ),
    path(
        "back/modules/<int:pk>/statut/",
        views.back_course_status,
        name="back_course_status",
    ),
    path(
        "back/modules/<int:course_pk>/ressources/nouveau/",
        views.back_resource_create,
        name="back_resource_create",
    ),
    path(
        "back/ressources/<int:pk>/modifier/",
        views.back_resource_edit,
        name="back_resource_edit",
    ),
    path(
        "back/ressources/<int:pk>/supprimer/",
        views.back_resource_delete,
        name="back_resource_delete",
    ),
    path(
        "back/modules/<int:course_pk>/quiz/nouveau/",
        views.back_quiz_create,
        name="back_quiz_create",
    ),
    path("back/quiz/", views.back_quizzes, name="back_quizzes"),
    path(
        "back/quiz/nouveau/",
        views.back_quiz_create_standalone,
        name="back_quiz_create_standalone",
    ),
    path("back/quiz/<int:pk>/", views.back_quiz_detail, name="back_quiz_detail"),
    path(
        "back/quiz/<int:pk>/modifier/",
        views.back_quiz_edit,
        name="back_quiz_edit",
    ),
    path(
        "back/quiz/<int:pk>/supprimer/",
        views.back_quiz_delete,
        name="back_quiz_delete",
    ),
    path(
        "back/quiz/<int:quiz_pk>/questions/nouveau/",
        views.back_question_create,
        name="back_question_create",
    ),
    path(
        "back/questions/<int:pk>/supprimer/",
        views.back_question_delete,
        name="back_question_delete",
    ),
    path("back/etudiants/", views.back_students, name="back_students"),
    # Console admin UniSphere
    path("console/", admin_views.admin_dashboard, name="admin_dashboard"),
    path("console/utilisateurs/", admin_views.admin_users, name="admin_users"),
    path(
        "console/utilisateurs/<int:pk>/",
        admin_views.admin_user_edit,
        name="admin_user_edit",
    ),
    path("console/modules/", admin_views.admin_courses, name="admin_courses"),
    path(
        "console/modules/nouveau/",
        admin_views.admin_course_create,
        name="admin_course_create",
    ),
    path(
        "console/modules/<int:pk>/modifier/",
        admin_views.admin_course_edit,
        name="admin_course_edit",
    ),
    path(
        "console/modules/<int:pk>/supprimer/",
        admin_views.admin_course_delete,
        name="admin_course_delete",
    ),
    path(
        "console/modules/<int:pk>/statut/",
        admin_views.admin_course_status,
        name="admin_course_status",
    ),
    path(
        "console/ressources/",
        admin_views.admin_resources,
        name="admin_resources",
    ),
    path(
        "console/ressources/nouveau/",
        admin_views.admin_resource_create,
        name="admin_resource_create",
    ),
    path(
        "console/ressources/<int:pk>/modifier/",
        admin_views.admin_resource_edit,
        name="admin_resource_edit",
    ),
    path(
        "console/ressources/<int:pk>/supprimer/",
        admin_views.admin_resource_delete,
        name="admin_resource_delete",
    ),
    path("console/quiz/", admin_views.admin_quizzes, name="admin_quizzes"),
    path(
        "console/quiz/nouveau/",
        admin_views.admin_quiz_create,
        name="admin_quiz_create",
    ),
    path(
        "console/quiz/<int:pk>/",
        admin_views.admin_quiz_detail,
        name="admin_quiz_detail",
    ),
    path(
        "console/quiz/<int:pk>/modifier/",
        admin_views.admin_quiz_edit,
        name="admin_quiz_edit",
    ),
    path(
        "console/quiz/<int:pk>/supprimer/",
        admin_views.admin_quiz_delete,
        name="admin_quiz_delete",
    ),
    path(
        "console/quiz/<int:quiz_pk>/questions/nouveau/",
        admin_views.admin_question_create,
        name="admin_question_create",
    ),
    path(
        "console/questions/<int:pk>/supprimer/",
        admin_views.admin_question_delete,
        name="admin_question_delete",
    ),
    path(
        "console/inscriptions/",
        admin_views.admin_enrollments,
        name="admin_enrollments",
    ),
    path(
        "console/inscriptions/<int:pk>/supprimer/",
        admin_views.admin_enrollment_delete,
        name="admin_enrollment_delete",
    ),
    path(
        "console/departements/",
        admin_views.admin_categories,
        name="admin_categories",
    ),
    path(
        "console/alertes/",
        admin_views.admin_notifications,
        name="admin_notifications",
    ),
]
