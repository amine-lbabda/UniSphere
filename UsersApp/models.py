from django.contrib.auth.models import AbstractUser
from django.db import models

# Create your models here.
ENUM_USERS = [("etudiant", "Etudiant"), ("enseignant", "Enseignant")]


class Utilisateur(AbstractUser):
    role = models.CharField(choices=ENUM_USERS, max_length=30)
    specialite = models.CharField(max_length=100)