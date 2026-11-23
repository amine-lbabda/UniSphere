from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse
from django.utils.text import slugify

from .programs import (
    PROGRAM_CHOICES,
    PROGRAM_FILIERE,
    PROGRAM_LABELS,
    PROGRAM_YEAR,
    filiere_label,
)


class UserProfile(models.Model):
    class Role(models.TextChoices):
        STUDENT = "student", "Étudiant"
        TEACHER = "teacher", "Enseignant"
        ADMIN = "admin", "Administrateur"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    role = models.CharField(
        "Rôle",
        max_length=20,
        choices=Role.choices,
        default=Role.STUDENT,
    )
    academic_level = models.CharField(
        "Parcours / spécialité",
        max_length=30,
        choices=PROGRAM_CHOICES,
        default="1A",
        blank=True,
        help_text="Choisi à la création du compte — détermine les modules affectés.",
    )
    student_id = models.CharField("Matricule", max_length=40, blank=True)

    class Meta:
        verbose_name = "Profil utilisateur"
        verbose_name_plural = "Profils utilisateurs"

    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"

    @property
    def is_student(self):
        return self.role == self.Role.STUDENT

    @property
    def is_teacher(self):
        return self.role in (self.Role.TEACHER, self.Role.ADMIN) or self.user.is_superuser

    @property
    def filiere(self):
        return PROGRAM_FILIERE.get(self.academic_level, "")

    @property
    def filiere_display(self):
        return filiere_label(self.academic_level)

    @property
    def year(self):
        return PROGRAM_YEAR.get(self.academic_level)

    def get_academic_level_display(self):
        return PROGRAM_LABELS.get(self.academic_level, self.academic_level or "—")



class Category(models.Model):
    name = models.CharField("Nom", max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    color = models.CharField(max_length=7, default="#3b5bdb")

    class Meta:
        verbose_name = "Catégorie / département"
        verbose_name_plural = "Catégories"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Course(models.Model):
    """Module universitaire (chaque enseignant est responsable de ses modules)."""

    class Status(models.TextChoices):
        DRAFT = "draft", "Brouillon"
        PUBLISHED = "published", "Publié"
        ARCHIVED = "archived", "Archivé"

    title = models.CharField("Titre du module", max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    code = models.CharField("Code module", max_length=20, unique=True)
    description = models.TextField("Description")
    short_description = models.CharField("Résumé", max_length=300, blank=True)
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="courses",
        verbose_name="Département / filière",
    )
    instructor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="taught_courses",
        verbose_name="Enseignant responsable",
    )
    cover = models.ImageField(
        "Couverture",
        upload_to="covers/",
        blank=True,
        null=True,
    )
    status = models.CharField(
        "Statut",
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
    )
    level = models.CharField(
        "Parcours cible",
        max_length=30,
        choices=PROGRAM_CHOICES,
        default="1A",
        help_text="Les étudiants de ce parcours (ex. 1A, 3IA, 4A-FINTECH, 2EM, 1GC) reçoivent ce module.",
    )
    duration_hours = models.PositiveIntegerField("Volume horaire", default=21)
    prerequisites = models.TextField(
        "Prérequis",
        blank=True,
        help_text="Texte libre : ce que ce module exige (compétences, cours, outils…).",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Module"
        verbose_name_plural = "Modules"
        ordering = ["-updated_at"]

    def __str__(self):
        return f"{self.code} — {self.title}"

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title)
            slug = base
            n = 1
            while Course.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{n}"
                n += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("courses:front_detail", kwargs={"slug": self.slug})

    @property
    def is_published(self):
        return self.status == self.Status.PUBLISHED

    @property
    def status_badge_class(self):
        return {
            self.Status.DRAFT: "badge-draft",
            self.Status.PUBLISHED: "badge-published",
            self.Status.ARCHIVED: "badge-archived",
        }.get(self.status, "")

    def get_level_display(self):
        return PROGRAM_LABELS.get(self.level, self.level)

    @property
    def filiere(self):
        return PROGRAM_FILIERE.get(self.level, "")

    @property
    def filiere_display(self):
        return filiere_label(self.level)



class Resource(models.Model):
    class ResourceType(models.TextChoices):
        PDF = "pdf", "PDF"
        VIDEO = "video", "Vidéo"
        LINK = "link", "Lien"
        DOCUMENT = "document", "Document"

    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="resources",
        verbose_name="Module",
    )
    title = models.CharField("Titre", max_length=200)
    resource_type = models.CharField(
        "Type",
        max_length=20,
        choices=ResourceType.choices,
        default=ResourceType.DOCUMENT,
    )
    description = models.TextField("Description", blank=True)
    file = models.FileField(
        "Fichier",
        upload_to="resources/",
        blank=True,
        null=True,
    )
    url = models.URLField("URL", blank=True)
    target_level = models.CharField(
        "Niveau destiné",
        max_length=30,
        choices=PROGRAM_CHOICES,
        blank=True,
        help_text="Parcours étudiant destinataire (ex. 1A, 3IA, 1EM). Par défaut = parcours du module.",
    )
    order = models.PositiveIntegerField("Ordre", default=0)
    is_required = models.BooleanField("Obligatoire", default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Ressource"
        verbose_name_plural = "Ressources"
        ordering = ["order", "created_at"]

    def __str__(self):
        return f"{self.title} ({self.get_resource_type_display()})"

    def save(self, *args, **kwargs):
        if not self.target_level and self.course_id:
            self.target_level = self.course.level
        super().save(*args, **kwargs)

    def get_target_level_display(self):
        return PROGRAM_LABELS.get(self.target_level, self.target_level or "—")

    @property
    def type_icon(self):
        return {
            self.ResourceType.PDF: "📄",
            self.ResourceType.VIDEO: "🎬",
            self.ResourceType.LINK: "🔗",
            self.ResourceType.DOCUMENT: "📎",
        }.get(self.resource_type, "📁")


class Enrollment(models.Model):
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="enrollments",
        verbose_name="Étudiant",
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="enrollments",
        verbose_name="Module",
    )
    enrolled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Inscription"
        verbose_name_plural = "Inscriptions"
        unique_together = ("student", "course")
        ordering = ["-enrolled_at"]

    def __str__(self):
        return f"{self.student} → {self.course.code}"


class Quiz(models.Model):
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="quizzes",
        verbose_name="Module",
    )
    title = models.CharField("Titre", max_length=200)
    description = models.TextField("Description", blank=True)
    duration_minutes = models.PositiveIntegerField("Durée (min)", default=15)
    passing_score = models.PositiveIntegerField("Seuil de réussite (%)", default=60)
    is_published = models.BooleanField("Publié", default=False)
    due_date = models.DateTimeField("Échéance", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Quiz"
        verbose_name_plural = "Quiz"
        ordering = ["-updated_at"]

    def __str__(self):
        return f"{self.title} ({self.course.code})"

    @property
    def question_count(self):
        return self.questions.count()


class Question(models.Model):
    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name="questions",
        verbose_name="Quiz",
    )
    text = models.TextField("Énoncé")
    points = models.PositiveIntegerField("Points", default=1)
    order = models.PositiveIntegerField("Ordre", default=0)

    class Meta:
        verbose_name = "Question"
        verbose_name_plural = "Questions"
        ordering = ["order", "id"]

    def __str__(self):
        return self.text[:60]


class Choice(models.Model):
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="choices",
        verbose_name="Question",
    )
    text = models.CharField("Réponse", max_length=400)
    is_correct = models.BooleanField("Correcte", default=False)

    class Meta:
        verbose_name = "Choix"
        verbose_name_plural = "Choix"

    def __str__(self):
        return self.text[:60]


class QuizAttempt(models.Model):
    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name="attempts",
        verbose_name="Quiz",
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="quiz_attempts",
        verbose_name="Étudiant",
    )
    score = models.FloatField("Score (%)", default=0)
    passed = models.BooleanField("Réussi", default=False)
    answers = models.JSONField("Réponses", default=dict, blank=True)
    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Tentative de quiz"
        verbose_name_plural = "Tentatives de quiz"
        ordering = ["-completed_at"]

    def __str__(self):
        return f"{self.student} — {self.quiz.title} ({self.score}%)"


class Notification(models.Model):
    class Level(models.TextChoices):
        INFO = "info", "Info"
        SUCCESS = "success", "Succès"
        WARNING = "warning", "Alerte"
        DEADLINE = "deadline", "Échéance"

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
        verbose_name="Destinataire",
    )
    title = models.CharField("Titre", max_length=200)
    message = models.TextField("Message")
    level = models.CharField(
        max_length=20,
        choices=Level.choices,
        default=Level.INFO,
    )
    link = models.CharField("Lien", max_length=300, blank=True)
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="notifications",
    )
    is_read = models.BooleanField("Lu", default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


def assign_modules_for_student(user):
    """Affecte automatiquement les modules publiés correspondant au parcours de l'étudiant."""
    try:
        profile = UserProfile.objects.get(user=user)
    except UserProfile.DoesNotExist:
        return []
    if not profile.is_student or not profile.academic_level:
        return []
    courses = Course.objects.filter(
        status=Course.Status.PUBLISHED,
        level=profile.academic_level,
    )
    created = []
    for course in courses:
        _, was_created = Enrollment.objects.get_or_create(student=user, course=course)
        if was_created:
            created.append(course)
    return created


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def ensure_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.get_or_create(user=instance)
