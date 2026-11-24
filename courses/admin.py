from django.contrib import admin

from .models import (
    Category,
    Choice,
    Course,
    CourseChapter,
    Enrollment,
    Notification,
    Question,
    Quiz,
    QuizAttempt,
    Resource,
    UserProfile,
)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "academic_level", "student_id", "phone")
    list_filter = ("role", "academic_level")
    search_fields = ("user__username", "user__email", "student_id", "phone")


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "color")
    prepopulated_fields = {"slug": ("name",)}


class ResourceInline(admin.TabularInline):
    model = Resource
    extra = 0


class CourseChapterInline(admin.TabularInline):
    model = CourseChapter
    extra = 0


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("code", "title", "status", "level", "instructor", "updated_at")
    list_filter = ("status", "level", "category")
    search_fields = ("title", "code", "description")
    prepopulated_fields = {"slug": ("title",)}
    inlines = [CourseChapterInline, ResourceInline]


@admin.register(CourseChapter)
class CourseChapterAdmin(admin.ModelAdmin):
    list_display = ("title", "course", "order", "created_at")
    list_filter = ("course",)
    search_fields = ("title", "course__code", "course__title")


@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "course",
        "chapter",
        "resource_type",
        "target_level",
        "order",
        "is_required",
    )
    list_filter = ("resource_type", "target_level", "is_required")
    search_fields = ("title", "course__title")


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ("student", "course", "enrolled_at")
    list_filter = ("course",)


class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 2


class QuestionInline(admin.StackedInline):
    model = Question
    extra = 0


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "course",
        "chapter",
        "order",
        "is_published",
        "passing_score",
        "due_date",
    )
    list_filter = ("is_published", "course")
    inlines = [QuestionInline]


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("text", "quiz", "points", "order")
    inlines = [ChoiceInline]


@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ("student", "quiz", "score", "passed", "completed_at")
    list_filter = ("passed", "quiz")


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("title", "recipient", "level", "is_read", "created_at")
    list_filter = ("level", "is_read")
