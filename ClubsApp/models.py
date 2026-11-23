from django.core.validators import MinLengthValidator
from django.db import models

# Create your models here.


class ClubsMembersBoard(models.Model):
    member = models.ForeignKey("UsersApp.Utilisateur", on_delete=models.CASCADE)
    club = models.ForeignKey("ClubsApp.Clubs", on_delete=models.CASCADE)
    board_role = models.CharField(max_length=100)


class Clubs(models.Model):
    name = models.CharField(
        max_length=100,
        validators=[MinLengthValidator(1, "A club name should never be empty !")],
    )
    description = models.TextField(
        max_length=100,
        validators=[MinLengthValidator(1, "A description should be provided !")],
    )
    Active = models.BooleanField(default=True)
    member_board = models.ManyToManyField(
        "UsersApp.Utilisateur", through=ClubsMembersBoard
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
