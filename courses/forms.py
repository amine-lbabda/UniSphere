from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

from .models import Category, Choice, Course, Question, Quiz, Resource, UserProfile
from .programs import (
    DEPARTMENT_SLUGS,
    Filiere,
    PROGRAM_CHOICES,
    PROGRAM_GROUPS,
    ensure_departments,
    programs_for_department,
    programs_for_filiere,
)


class ProgramSelect(forms.Select):
    """Select with optgroups for parcours académiques."""

    def __init__(self, attrs=None):
        super().__init__(attrs=attrs, choices=PROGRAM_GROUPS)


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = [
            "title",
            "code",
            "short_description",
            "description",
            "category",
            "cover",
            "status",
            "level",
            "duration_hours",
            "prerequisites",
        ]
        widgets = {
            "title": forms.TextInput(attrs={"placeholder": "Ex. Programmation Python"}),
            "code": forms.TextInput(attrs={"placeholder": "Ex. INF101"}),
            "short_description": forms.TextInput(
                attrs={"placeholder": "Résumé du module"}
            ),
            "description": forms.Textarea(attrs={"rows": 6}),
            "prerequisites": forms.Textarea(
                attrs={
                    "rows": 3,
                    "placeholder": "Ex. Bases d’algorithmique, INF101, notions de maths…",
                }
            ),
            "duration_hours": forms.NumberInput(attrs={"min": 1}),
            "level": forms.Select(),
            "category": forms.Select(attrs={"id": "id_category"}),
        }
        labels = {
            "category": "Département",
            "level": "Niveau destiné",
            "prerequisites": "Prérequis (texte libre)",
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        include_instructor = kwargs.pop("include_instructor", False)
        ensure_departments()
        super().__init__(*args, **kwargs)
        self._user = user
        self._include_instructor = include_instructor

        # Uniquement les 4 départements officiels (ordre fixe)
        from django.db.models import Case, IntegerField, When

        preserved = Case(
            *[When(slug=s, then=i) for i, s in enumerate(DEPARTMENT_SLUGS)],
            output_field=IntegerField(),
        )
        self.fields["category"].queryset = Category.objects.filter(
            slug__in=DEPARTMENT_SLUGS
        ).order_by(preserved)
        self.fields["category"].required = True
        self.fields["category"].empty_label = "Choisir un département"
        self.fields["category"].widget.attrs["id"] = "id_category"

        # Niveaux filtrés selon le département sélectionné
        dept_slug = None
        if self.data.get("category"):
            try:
                cat = Category.objects.get(pk=self.data.get("category"))
                dept_slug = cat.slug
            except (Category.DoesNotExist, ValueError, TypeError):
                dept_slug = None
        elif self.instance and self.instance.pk and self.instance.category_id:
            dept_slug = self.instance.category.slug
        elif self.initial.get("category"):
            try:
                cat = self.initial["category"]
                dept_slug = cat.slug if hasattr(cat, "slug") else Category.objects.get(pk=cat).slug
            except Exception:
                dept_slug = None

        level_choices = programs_for_department(dept_slug) if dept_slug else []
        self.fields["level"].choices = [("", "Choisir d’abord un département")] + level_choices
        self.fields["level"].required = True
        self.fields["level"].help_text = (
            "Les niveaux proposés dépendent du département choisi."
        )
        self.fields["level"].widget.attrs["id"] = "id_level"
        self.fields["prerequisites"].required = False
        self.fields["prerequisites"].help_text = (
            "Indiquez librement ce que ce module exige — pas de liste fermée."
        )
        if include_instructor:
            from django.db.models import Q

            User = get_user_model()
            self.fields["instructor"] = forms.ModelChoiceField(
                label="Enseignant responsable",
                queryset=User.objects.filter(
                    Q(profile__role=UserProfile.Role.TEACHER)
                    | Q(profile__role=UserProfile.Role.ADMIN)
                    | Q(is_staff=True)
                )
                .distinct()
                .order_by("last_name", "first_name", "username"),
                required=True,
                widget=forms.Select(attrs={"class": "form-control"}),
            )
            if self.instance and self.instance.pk and self.instance.instructor_id:
                self.fields["instructor"].initial = self.instance.instructor_id
        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxInput):
                continue
            css = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = f"{css} form-control".strip()

    def clean(self):
        cleaned = super().clean()
        category = cleaned.get("category")
        level = cleaned.get("level")
        if category and level:
            allowed = {c for c, _ in programs_for_department(category.slug)}
            if level not in allowed:
                self.add_error(
                    "level",
                    "Ce niveau ne correspond pas au département sélectionné.",
                )
        return cleaned


class ResourceForm(forms.ModelForm):
    class Meta:
        model = Resource
        fields = [
            "title",
            "resource_type",
            "description",
            "file",
            "url",
            "target_level",
            "order",
            "is_required",
        ]
        widgets = {
            "title": forms.TextInput(attrs={"placeholder": "Titre de la ressource"}),
            "description": forms.Textarea(attrs={"rows": 3}),
            "url": forms.URLInput(attrs={"placeholder": "https://..."}),
            "order": forms.NumberInput(attrs={"min": 0}),
            "target_level": ProgramSelect(),
        }
        labels = {
            "target_level": "Niveau destiné (étudiants)",
        }

    def __init__(self, *args, **kwargs):
        course = kwargs.pop("course", None)
        include_course = kwargs.pop("include_course", False)
        super().__init__(*args, **kwargs)
        self.fields["target_level"].choices = PROGRAM_GROUPS
        self.fields["target_level"].required = True
        if include_course:
            self.fields["course"] = forms.ModelChoiceField(
                label="Module",
                queryset=Course.objects.select_related("instructor").order_by("code"),
                required=True,
                widget=forms.Select(attrs={"class": "form-control"}),
            )
            if course:
                self.fields["course"].initial = course.pk
            elif self.instance and self.instance.pk:
                self.fields["course"].initial = self.instance.course_id
        if course and not self.initial.get("target_level") and not self.instance.pk:
            self.initial["target_level"] = course.level
        elif self.instance and self.instance.pk and not self.instance.target_level and course:
            self.initial["target_level"] = course.level
        for name, field in self.fields.items():
            if name == "is_required":
                field.widget.attrs["class"] = "form-check-input"
            else:
                css = field.widget.attrs.get("class", "")
                field.widget.attrs["class"] = f"{css} form-control".strip()

    def clean(self):
        cleaned = super().clean()
        rtype = cleaned.get("resource_type")
        file = cleaned.get("file")
        url = cleaned.get("url")
        if rtype == Resource.ResourceType.LINK and not url:
            self.add_error("url", "Une URL est requise pour un lien.")
        if rtype in (
            Resource.ResourceType.PDF,
            Resource.ResourceType.DOCUMENT,
            Resource.ResourceType.VIDEO,
        ) and not file and not (self.instance and self.instance.file):
            if not url:
                self.add_error(
                    "file",
                    "Ajoutez un fichier ou une URL pour cette ressource.",
                )
        if not cleaned.get("target_level"):
            self.add_error("target_level", "Indiquez le niveau destiné.")
        return cleaned


class CourseFilterForm(forms.Form):
    q = forms.CharField(
        required=False,
        label="Recherche",
        widget=forms.TextInput(
            attrs={
                "placeholder": "Rechercher un module…",
                "class": "form-control search-input",
            }
        ),
    )
    category = forms.ModelChoiceField(
        queryset=None,
        required=False,
        empty_label="Tous les départements",
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    level = forms.ChoiceField(
        required=False,
        choices=[("", "Tous les parcours")] + PROGRAM_CHOICES,
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    status = forms.ChoiceField(
        required=False,
        choices=[("", "Tous les statuts")] + list(Course.Status.choices),
        widget=forms.Select(attrs={"class": "form-control"}),
    )

    def __init__(self, *args, **kwargs):
        from django.db.models import Case, IntegerField, When

        from .models import Category
        from .programs import DEPARTMENT_SLUGS, ensure_departments

        ensure_departments()
        super().__init__(*args, **kwargs)
        preserved = Case(
            *[When(slug=s, then=i) for i, s in enumerate(DEPARTMENT_SLUGS)],
            output_field=IntegerField(),
        )
        self.fields["category"].queryset = Category.objects.filter(
            slug__in=DEPARTMENT_SLUGS
        ).order_by(preserved)
        self.fields["level"].choices = [("", "Tous les parcours")] + [
            (group, opts) for group, opts in PROGRAM_GROUPS
        ]


class StudentRegistrationForm(UserCreationForm):
    first_name = forms.CharField(
        label="Prénom",
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    last_name = forms.CharField(
        label="Nom",
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={"class": "form-control"}),
    )
    student_id = forms.CharField(
        label="Matricule",
        required=False,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Ex. ESP-2024-001"}
        ),
    )
    filiere = forms.ChoiceField(
        label="Filière",
        choices=Filiere.CHOICES,
        widget=forms.Select(attrs={"class": "form-control", "id": "id_filiere"}),
    )
    academic_level = forms.ChoiceField(
        label="Année / spécialité",
        choices=PROGRAM_CHOICES,
        widget=forms.Select(attrs={"class": "form-control", "id": "id_academic_level"}),
    )

    class Meta:
        model = get_user_model()
        fields = (
            "username",
            "first_name",
            "last_name",
            "email",
            "password1",
            "password2",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in ("username", "password1", "password2"):
            self.fields[name].widget.attrs["class"] = "form-control"
        # Default program list = Info; JS will filter by filière
        self.fields["academic_level"].choices = programs_for_filiere(Filiere.INFO)

        # If POST includes filiere, rebuild program choices for validation
        if self.data.get("filiere"):
            self.fields["academic_level"].choices = programs_for_filiere(
                self.data.get("filiere")
            )

    def clean(self):
        cleaned = super().clean()
        filiere = cleaned.get("filiere")
        program = cleaned.get("academic_level")
        valid = {code for code, _ in programs_for_filiere(filiere or "")}
        if program and program not in valid:
            self.add_error(
                "academic_level",
                "Ce parcours ne correspond pas à la filière choisie.",
            )
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.role = UserProfile.Role.STUDENT
            profile.academic_level = self.cleaned_data["academic_level"]
            profile.student_id = self.cleaned_data.get("student_id", "")
            profile.save()
            # Évite le cache OneToOne créé par le signal (défaut 1A)
            user.profile = profile
        return user


class QuizForm(forms.ModelForm):
    class Meta:
        model = Quiz
        fields = [
            "title",
            "description",
            "duration_minutes",
            "passing_score",
            "is_published",
            "due_date",
        ]
        widgets = {
            "title": forms.TextInput(attrs={"placeholder": "Ex. Contrôle continu n°1"}),
            "description": forms.Textarea(attrs={"rows": 3}),
            "duration_minutes": forms.NumberInput(attrs={"min": 1}),
            "passing_score": forms.NumberInput(attrs={"min": 0, "max": 100}),
            "due_date": forms.DateTimeInput(
                attrs={"type": "datetime-local"},
                format="%Y-%m-%dT%H:%M",
            ),
        }

    def __init__(self, *args, **kwargs):
        include_course = kwargs.pop("include_course", False)
        course = kwargs.pop("course", None)
        course_queryset = kwargs.pop("course_queryset", None)
        super().__init__(*args, **kwargs)
        self.fields["due_date"].input_formats = ["%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M:%S"]
        if include_course:
            qs = course_queryset
            if qs is None:
                qs = Course.objects.select_related("instructor").order_by("code")
            self.fields["course"] = forms.ModelChoiceField(
                label="Module",
                queryset=qs,
                required=True,
                widget=forms.Select(attrs={"class": "form-control"}),
            )
            if course:
                self.fields["course"].initial = course.pk
            elif self.instance and self.instance.pk:
                self.fields["course"].initial = self.instance.course_id
        for name, field in self.fields.items():
            if name == "is_published":
                field.widget.attrs["class"] = "form-check-input"
            else:
                css = field.widget.attrs.get("class", "")
                field.widget.attrs["class"] = f"{css} form-control".strip()


class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ["text", "points", "order"]
        widgets = {
            "text": forms.Textarea(attrs={"rows": 3, "placeholder": "Énoncé de la question"}),
            "points": forms.NumberInput(attrs={"min": 1}),
            "order": forms.NumberInput(attrs={"min": 0}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            css = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = f"{css} form-control".strip()


class ChoiceForm(forms.ModelForm):
    class Meta:
        model = Choice
        fields = ["text", "is_correct"]
        widgets = {
            "text": forms.TextInput(attrs={"placeholder": "Texte du choix"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["text"].widget.attrs["class"] = "form-control"
        self.fields["is_correct"].widget.attrs["class"] = "form-check-input"


ChoiceFormSet = forms.inlineformset_factory(
    Question,
    Choice,
    form=ChoiceForm,
    extra=4,
    min_num=2,
    validate_min=True,
    can_delete=True,
)
