from django.utils.translation import gettext_lazy as _

# Порядок уровней от простого к сложному — используется в алгоритмах взвешивания графа
SKILL_LEVELS = ["beginner", "intermediate", "advanced", "expert"]

# Django choices для полей CharField в моделях
LEVEL_CHOICES = [
    ("beginner", _("Beginner")),
    ("intermediate", _("Intermediate")),
    ("advanced", _("Advanced")),
    ("expert", _("Expert")),
]

# Допустимые типы связей между навыками в графе
RELATION_TYPES = frozenset({"DEPENDS_ON", "RELATED_TO"})
