from django.core.validators import MinLengthValidator
from django.db import models

# Create your models here.


class Evenements(models.Model):
    title = models.CharField(
        max_length=40,
        verbose_name="Titre",
        validators=[
            MinLengthValidator(1, "An event should never have an empty title !")
        ],
    )
    description = models.TextField(
        max_length=100,
        verbose_name="Description",
        validators=[MinLengthValidator(1, "An event should have a description !")],
    )
    start_date = models.DateField(verbose_name="Date de début")
    end_date = models.DateField(verbose_name="Date de fin")
    type_evenement = models.CharField(
        choices=[("online", "Online"), ("onsite", "OnSite")],
        max_length=200,
        default="online",
        verbose_name="Type d'événement",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    participants = models.ManyToManyField(
        "UsersApp.Utilisateur",
        verbose_name="Participant",
    )
