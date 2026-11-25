from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand
from django.utils import timezone

from courses.models import (
    Category,
    Choice,
    Course,
    Enrollment,
    Notification,
    Question,
    Quiz,
    Resource,
    UserProfile,
    assign_modules_for_student,
)


class Command(BaseCommand):
    help = "Comptes UniSphere + modules par parcours (1A…5A / EM / GC)"

    def handle(self, *args, **options):
        User = get_user_model()
        teachers_g, _ = Group.objects.get_or_create(name="Enseignants")
        students_g, _ = Group.objects.get_or_create(name="Etudiants")

        def upsert_user(
            username,
            password,
            first,
            last,
            email,
            *,
            role,
            program="",
            student_id="",
            staff=False,
            superuser=False,
            groups=None,
        ):
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    "email": email,
                    "first_name": first,
                    "last_name": last,
                    "is_staff": staff or superuser,
                    "is_superuser": superuser,
                },
            )
            user.set_password(password)
            user.first_name = first
            user.last_name = last
            user.email = email
            user.is_staff = staff or superuser
            user.is_superuser = superuser
            user.save()
            if groups:
                user.groups.set(groups)
            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.role = role
            profile.academic_level = program or ""
            profile.student_id = student_id
            profile.save()
            self.stdout.write(
                f"  · {username} [{role}] {program or '—'} "
                f"({'créé' if created else 'MAJ'})"
            )
            return user

        self.stdout.write("Comptes…")
        upsert_user(
            "admin", "Admin@2024", "Admin", "UniSphere",
            "admin@unisphere.local",
            role=UserProfile.Role.ADMIN, staff=True, superuser=True,
        )
        teacher1 = upsert_user(
            "enseignant", "edu2024", "Arwa", "Ben Salem",
            "arwa.bensalem@unisphere.local",
            role=UserProfile.Role.TEACHER, staff=True, groups=[teachers_g],
        )
        teacher2 = upsert_user(
            "enseignant2", "edu2024", "Karim", "Trabelsi",
            "karim.trabelsi@unisphere.local",
            role=UserProfile.Role.TEACHER, staff=True, groups=[teachers_g],
        )

        # Étudiants — différents parcours
        s_1a = upsert_user(
            "etudiant1", "etu2024", "Sara", "Mansouri",
            "sara.mansouri@esprit.tn",
            role=UserProfile.Role.STUDENT, program="1A",
            student_id="ESP-2024-001", groups=[students_g],
        )
        s_2a = upsert_user(
            "etudiant2", "etu2024", "Youssef", "Gharbi",
            "youssef.gharbi@esprit.tn",
            role=UserProfile.Role.STUDENT, program="2A",
            student_id="ESP-2023-014", groups=[students_g],
        )
        s_3ia = upsert_user(
            "etudiant3", "etu2024", "Ines", "Bouaziz",
            "ines.bouaziz@esprit.tn",
            role=UserProfile.Role.STUDENT, program="3IA",
            student_id="ESP-2022-022", groups=[students_g],
        )
        s_4fin = upsert_user(
            "etudiant4", "etu2024", "Amine", "Khelifi",
            "amine.khelifi@esprit.tn",
            role=UserProfile.Role.STUDENT, program="4A-FINTECH",
            student_id="ESP-2021-044", groups=[students_g],
        )
        s_1em = upsert_user(
            "etudiant_em", "etu2024", "Nour", "Jebali",
            "nour.jebali@esprit.tn",
            role=UserProfile.Role.STUDENT, program="1EM",
            student_id="ESP-2024-EM01", groups=[students_g],
        )
        s_1gc = upsert_user(
            "etudiant_gc", "etu2024", "Omar", "Sassi",
            "omar.sassi@esprit.tn",
            role=UserProfile.Role.STUDENT, program="1GC",
            student_id="ESP-2024-GC01", groups=[students_g],
        )

        from courses.programs import ensure_departments

        cats = ensure_departments()
        # aliases pour le seed
        cats["Informatique"] = cats["informatique"]
        cats["Tronc-Commun"] = cats["tronc-commun"]
        cats["Électromécanique"] = cats["em"]
        cats["Génie Civil"] = cats["gc"]

        Quiz.objects.all().delete()
        Resource.objects.all().delete()
        Enrollment.objects.all().delete()
        Notification.objects.all().delete()
        Course.objects.all().delete()

        def pub(**kwargs):
            kwargs.setdefault("status", Course.Status.PUBLISHED)
            kwargs.setdefault("published_at", timezone.now())
            return Course.objects.create(**kwargs)

        # Info TC
        c_1a = pub(
            title="Programmation Python", code="INF101",
            short_description="Bases Python — 1A tronc commun Info.",
            description="Module 1A : variables, structures, fonctions.",
            category=cats["Tronc-Commun"], instructor=teacher1,
            level="1A", duration_hours=42,
            prerequisites="Notions de logique et d’algorithmique de base.",
        )
        pub(
            title="Algèbre linéaire", code="MAT150",
            short_description="Vecteurs et matrices — 1A.",
            description="Mathématiques pour le tronc commun Info 1A.",
            category=cats["Tronc-Commun"], instructor=teacher2,
            level="1A", duration_hours=42,
            prerequisites="Mathématiques du lycée (algèbre, géométrie).",
        )
        c_2a = pub(
            title="Structures de données", code="INF210",
            short_description="Listes, arbres, complexité — 2A.",
            description="Module 2A tronc commun Informatique.",
            category=cats["Tronc-Commun"], instructor=teacher1,
            level="2A", duration_hours=42,
            prerequisites="INF101 — Programmation Python ; bases d’algorithmique.",
        )
        # 3A / 3IA
        pub(
            title="Génie logiciel", code="INF310",
            short_description="Cycle de vie logiciel — 3A.",
            description="Continuité tronc commun en 3ème année Info.",
            category=cats["Informatique"], instructor=teacher1,
            level="3A", duration_hours=42,
            prerequisites="INF210 — Structures de données ; travail en équipe.",
        )
        c_3ia = pub(
            title="Machine Learning", code="IA320",
            short_description="Apprentissage automatique — 3IA.",
            description="Spécialité Intelligence Artificielle (3IA).",
            category=cats["Informatique"], instructor=teacher1,
            level="3IA", duration_hours=63,
            prerequisites="Python, algèbre linéaire, probabilités ; idéalement INF210.",
        )
        # 4A spécialités Info
        c_4fin = pub(
            title="Blockchain & Fintech", code="FIN410",
            short_description="Finance digitale — 4A Fintech.",
            description="Spécialité Fintech 4ème année.",
            category=cats["Informatique"], instructor=teacher1,
            level="4A-FINTECH", duration_hours=42,
            prerequisites="Bases de cryptographie et d’architecture distribuée.",
        )
        pub(
            title="Data Architecture", code="DAS410",
            short_description="Architectures data — 4A DAS-info.",
            description="Spécialité DAS-info 4ème année.",
            category=cats["Informatique"], instructor=teacher1,
            level="4A-DAS", duration_hours=42,
        )
        # EM
        pub(
            title="Résistance des matériaux", code="EM110",
            short_description="RDM introductive — 1EM.",
            description="Module 1ère année Électromécanique.",
            category=cats["Électromécanique"], instructor=teacher2,
            level="1EM", duration_hours=42,
        )
        pub(
            title="Conception OGI", code="OGI410",
            short_description="Organisation et gestion industrielle — 4A OGI.",
            description="Spécialité OGI (4ème année EM).",
            category=cats["Électromécanique"], instructor=teacher2,
            level="4EM-OGI", duration_hours=42,
        )
        # GC
        pub(
            title="Matériaux de construction", code="GC110",
            short_description="Béton, acier, bois — 1GC.",
            description="Module 1ère année Génie Civil.",
            category=cats["Génie Civil"], instructor=teacher2,
            level="1GC", duration_hours=42,
        )
        Course.objects.create(
            title="Anglais technique", code="ANG110",
            short_description="Brouillon enseignant.",
            description="Module en préparation.",
            category=cats["Tronc-Commun"], instructor=teacher2,
            status=Course.Status.DRAFT, level="1A", duration_hours=21,
        )

        Resource.objects.create(
            course=c_1a, title="Syllabus INF101",
            resource_type=Resource.ResourceType.PDF,
            url="https://example.com/syllabus-inf101.pdf",
            target_level="1A", order=1, is_required=True,
        )
        Resource.objects.create(
            course=c_1a, title="Vidéo — Variables",
            resource_type=Resource.ResourceType.VIDEO,
            url="https://www.youtube.com/watch?v=rfscVS0vtbw",
            target_level="1A", order=2,
        )
        Resource.objects.create(
            course=c_3ia, title="Cours ML — intro",
            resource_type=Resource.ResourceType.LINK,
            url="https://scikit-learn.org/stable/tutorial/basic/tutorial.html",
            target_level="3IA", order=1, is_required=True,
        )

        quiz = Quiz.objects.create(
            course=c_1a, title="CC Python n°1",
            description="QCM bases Python (1A).",
            duration_minutes=20, passing_score=60, is_published=True,
            due_date=timezone.now() + timedelta(days=14),
        )
        q1 = Question.objects.create(
            quiz=quiz, text="Mot-clé pour définir une fonction ?", points=1, order=1
        )
        Choice.objects.create(question=q1, text="function", is_correct=False)
        Choice.objects.create(question=q1, text="def", is_correct=True)
        Choice.objects.create(question=q1, text="fun", is_correct=False)
        q2 = Question.objects.create(
            quiz=quiz, text="Type d’une liste mutable ?", points=1, order=2
        )
        Choice.objects.create(question=q2, text="tuple", is_correct=False)
        Choice.objects.create(question=q2, text="list", is_correct=True)
        Choice.objects.create(question=q2, text="set", is_correct=False)

        for s in (s_1a, s_2a, s_3ia, s_4fin, s_1em, s_1gc):
            assign_modules_for_student(s)

        Notification.objects.create(
            recipient=s_1a,
            title="Bienvenue — 1A Info",
            message="Modules du tronc commun 1A affectés automatiquement.",
            level=Notification.Level.SUCCESS, link="/etudiant/",
        )
        Notification.objects.create(
            recipient=s_3ia,
            title="Parcours 3IA",
            message="Vos modules IA (ex. Machine Learning) sont disponibles.",
            level=Notification.Level.INFO, link="/etudiant/",
        )
        Notification.objects.create(
            recipient=teacher1,
            title="Espace enseignant",
            message="Assignez chaque module à un parcours (1A, 3IA, 4A-FINTECH, 1EM, 1GC…).",
            level=Notification.Level.INFO, link="/back/",
        )

        self.stdout.write(self.style.SUCCESS("Seed parcours académiques terminé."))
