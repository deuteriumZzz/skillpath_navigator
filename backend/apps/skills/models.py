from django.db import models
from django.conf import settings

class Skill(models.Model):
    LEVEL_CHOICES = [
        ('beginner', 'Новичок'),
        ('intermediate', 'Средний'),
        ('advanced', 'Продвинутый'),
    ]

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='skills',
        on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_verified = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} ({self.get_level_display()})"

class SkillTag(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name

class SkillTagRelation(models.Model):
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE)
    tag = models.ForeignKey(SkillTag, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('skill', 'tag')
