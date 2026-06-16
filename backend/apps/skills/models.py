from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.utils.translation import gettext_lazy as _
from apps.users.models import User
from apps.graph.services import add_skill_to_graph

class Skill(models.Model):
    LEVEL_CHOICES = [
        ('beginner', _('Beginner')),
        ('intermediate', _('Intermediate')),
        ('advanced', _('Advanced')),
        ('expert', _('Expert')),
    ]

    name = models.CharField(max_length=100, unique=True, verbose_name=_('Название навыка'))
    description = models.TextField(blank=True, verbose_name=_('Описание'))
    level = models.CharField(
        max_length=20,
        choices=LEVEL_CHOICES,
        default='beginner',
        verbose_name=_('Уровень')
    )
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='skills',
        verbose_name=_('Владелец')
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Дата создания'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Дата обновления'))
    dependencies = ArrayField(
        models.CharField(max_length=100),
        blank=True,
        default=list,
        verbose_name=_('Зависимости')
    )
    related_skills = ArrayField(
        models.CharField(max_length=100),
        blank=True,
        default=list,
        verbose_name=_('Связанные навыки')
    )
    is_verified = models.BooleanField(default=False, verbose_name=_('Проверенный навык'))
    tags = ArrayField(
        models.CharField(max_length=50),
        blank=True,
        default=list,
        verbose_name=_('Теги')
    )

    class Meta:
        verbose_name = _('Навык')
        verbose_name_plural = _('Навыки')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['level']),
        ]

    def save(self, *args, **kwargs):
        # Добавляем навык в граф Neo4j при сохранении
        if not self.pk:
            add_skill_to_graph(self.name, self.level)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
