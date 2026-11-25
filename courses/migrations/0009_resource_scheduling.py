from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ("courses", "0008_course_chapters_builder"),
    ]

    operations = [
        migrations.AddField(
            model_name="resource",
            name="scheduled_at",
            field=models.DateTimeField(
                blank=True,
                help_text="Si défini dans le futur, la ressource reste invisible jusqu’à cette date.",
                null=True,
                verbose_name="Publication programmée",
            ),
        ),
        migrations.AddField(
            model_name="resource",
            name="updated_at",
            field=models.DateTimeField(
                auto_now=True, default=django.utils.timezone.now
            ),
            preserve_default=False,
        ),
    ]
