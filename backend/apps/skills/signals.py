from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender="skills.Skill")
def sync_skill_to_graph(sender, instance, created, **kwargs):
    from core.constants import SKILL_GRAPH_CACHE_KEY
    from django.core.cache import cache

    if created:
        from apps.graph.services import add_skill_to_graph

        add_skill_to_graph(instance.name, instance.level)
    cache.delete(SKILL_GRAPH_CACHE_KEY)
