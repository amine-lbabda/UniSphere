from django.db import migrations, models
import django.db.models.deletion
from django.core.validators import MinLengthValidator


class Migration(migrations.Migration):

    dependencies = [
        ("EventsApp", "0004_remove_clubsmembersboard_club_and_more"),
        ("UsersApp", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="evenements",
            name="title",
            field=models.CharField(
                max_length=40,
                validators=[
                    MinLengthValidator(1, "An event should never have an empty title !")
                ],
                verbose_name="Titre",
            ),
        ),
        migrations.AlterField(
            model_name="evenements",
            name="description",
            field=models.TextField(
                max_length=100,
                validators=[
                    MinLengthValidator(1, "An event should have a description !")
                ],
                verbose_name="Description",
            ),
        ),
        migrations.AlterField(
            model_name="evenements",
            name="start_date",
            field=models.DateField(verbose_name="Date de début"),
        ),
        migrations.AlterField(
            model_name="evenements",
            name="end_date",
            field=models.DateField(verbose_name="Date de fin"),
        ),
        migrations.AlterField(
            model_name="evenements",
            name="type_evenement",
            field=models.CharField(
                choices=[("online", "Online"), ("onsite", "OnSite")],
                default="online",
                max_length=200,
                verbose_name="Type d'événement",
            ),
        ),
        migrations.AlterField(
            model_name="evenements",
            name="participants",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to="UsersApp.utilisateur",
                verbose_name="Participant",
            ),
        ),
    ]
