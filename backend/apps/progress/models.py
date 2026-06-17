from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _


class UserSkillProgress(models.Model):
    """Процент прохождения навыка пользователем (POST /api/progress/update/)."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="progress_entries",
        verbose_name=_("Пользователь"),
    )
    skill = models.ForeignKey(
        "skills.Skill",
        on_delete=models.CASCADE,
        related_name="progress_entries",
        verbose_name=_("Навык"),
    )
    completion_percent = models.PositiveSmallIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name=_("Процент прохождения"),
    )
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Обновлено"))

    class Meta:
        verbose_name = _("Прогресс по навыку")
        verbose_name_plural = _("Прогресс по навыкам")
        unique_together = ("user", "skill")
        ordering = ["-updated_at"]

    def __str__(self):
        return f"{self.user} — {self.skill}: {self.completion_percent}%"
