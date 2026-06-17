import django_filters

from .models import Skill


class SkillFilter(django_filters.FilterSet):
    """Фильтры для списка навыков: поиск по имени (без учёта регистра), тегу, уровню и статусу верификации."""

    name = django_filters.CharFilter(lookup_expr="icontains")
    tag = django_filters.CharFilter(method="filter_by_tag")

    class Meta:
        model = Skill
        fields = ["level", "is_verified"]

    def filter_by_tag(self, queryset, name, value):
        """Фильтрует навыки, у которых массив tags содержит переданное значение."""
        return queryset.filter(tags__contains=[value])
