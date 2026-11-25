from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("courses", "0007_course_resource_visibility"),
    ]

    operations = [
        migrations.CreateModel(
            name="CourseChapter",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("title", models.CharField(max_length=200, verbose_name="Titre du chapitre")),
                ("order", models.PositiveIntegerField(default=0, verbose_name="Ordre")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "course",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="chapters",
                        to="courses.course",
                        verbose_name="Cours",
                    ),
                ),
            ],
            options={
                "verbose_name": "Chapitre",
                "verbose_name_plural": "Chapitres",
                "ordering": ["order", "id"],
            },
        ),
        migrations.AddField(
            model_name="resource",
            name="chapter",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="resources",
                to="courses.coursechapter",
                verbose_name="Chapitre",
            ),
        ),
        migrations.AddField(
            model_name="quiz",
            name="chapter",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="quizzes",
                to="courses.coursechapter",
                verbose_name="Chapitre",
            ),
        ),
        migrations.AddField(
            model_name="quiz",
            name="order",
            field=models.PositiveIntegerField(default=0, verbose_name="Ordre"),
        ),
        migrations.AlterModelOptions(
            name="quiz",
            options={
                "ordering": ["order", "-updated_at"],
                "verbose_name": "Quiz",
                "verbose_name_plural": "Quiz",
            },
        ),
    ]
