from django.core.exceptions import ValidationError
from django.core.validators import MinLengthValidator
from django.db import models
from django.utils import timezone

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
    paid_event = models.BooleanField(default=False)
    price_participation = models.FloatField(default=0)
    latitude = models.FloatField(default=0)
    longitude = models.FloatField(default=0)

    def clean(self):
        super().clean()
        if self.start_date > self.end_date:
            raise ValidationError(
                "The end date must be on or after the start date."
            )
        elif (
            self.start_date < timezone.localdate()
            or self.end_date < timezone.localdate()
        ):
            raise ValidationError("Forbidden: Cannot set an event in the past !")
        if self.paid_event and self.price_participation == 0:
            raise ValidationError("Forbidden: You must set a price !")
        if self.latitude == 0 and self.longitude == 0:
            raise ValidationError("Forbidden: You must set an event place !")
