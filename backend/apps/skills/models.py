from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

LEVEL_CHOICES = [
    ('beginner', _('Beginner')),
    ('intermediate', _('Intermediate')),
    ('advanced', _('Advanced')),
    ('expert', _('Expert')),
]


class Skill(models.Model):
    """Узел графа навыков (каталог). Уровень здесь — собственная сложность навыка,
    используется графовыми алгоритмами для расчёта веса перехода между навыками."""

    name = models.CharField(max_length=100, unique=True, verbose_name=_('Название навыка'))
    description = models.TextField(blank=True, verbose_name=_('Описание'))
    level = models.CharField(
        max_length=20,
        choices=LEVEL_CHOICES,
        default='beginner',
        verbose_name=_('Уровень'),
    )
    tags = models.JSONField(default=list, blank=True, verbose_name=_('Теги'))
    is_verified = models.BooleanField(default=False, verbose_name=_('Проверенный навык'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Дата создания'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Дата обновления'))

    class Meta:
        verbose_name = _('Навык')
        verbose_name_plural = _('Навыки')
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['level']),
        ]

    def save(self, *args, **kwargs):
        from apps.graph.services import add_skill_to_graph

        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new:
            add_skill_to_graph(self.name, self.level)

    def __str__(self):
        return self.name


class UserSkill(models.Model):
    """Навык, которым владеет конкретный пользователь, с его собственным уровнем."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='user_skills',
        verbose_name=_('Пользователь'),
    )
    skill = models.ForeignKey(
        Skill,
        on_delete=models.CASCADE,
        related_name='user_skills',
        verbose_name=_('Навык'),
    )
    level = models.CharField(
        max_length=20,
        choices=LEVEL_CHOICES,
        default='beginner',
        verbose_name=_('Уровень владения'),
    )
    acquired_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Дата добавления'))

    class Meta:
        verbose_name = _('Навык пользователя')
        verbose_name_plural = _('Навыки пользователя')
        unique_together = ('user', 'skill')
        ordering = ['-acquired_at']

    def __str__(self):
        return f"{self.user} — {self.skill} ({self.level})"
