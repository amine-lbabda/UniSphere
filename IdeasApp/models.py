from django.conf import settings
from django.db import models


class Idea(models.Model):
    TYPE_CHOICES = [('suggestion', 'Suggestion'),('reclamation', 'Réclamation'),]
    STATUS_CHOICES = [('pending', 'En attente'),('accepted', 'Validée'),('rejected', 'Rejetée'),]

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='ideas',
    )
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    title = models.CharField(max_length=200)
    content = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.get_type_display()})"