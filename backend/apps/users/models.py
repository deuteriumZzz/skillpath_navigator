from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    email = models.EmailField(unique=True)
    avatar = models.URLField(blank=True, null=True)
    bio = models.TextField(blank=True)

    def __str__(self):
        return f"{self.username} ({self.email})"
