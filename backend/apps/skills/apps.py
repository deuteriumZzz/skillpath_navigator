from django.apps import AppConfig


class SkillsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.skills"
    label = "skills"

    def ready(self):
        import apps.skills.signals  # noqa: F401

        from django.db.utils import OperationalError, ProgrammingError

        try:
            from apps.graph.services import GraphService
            from apps.skills.models import Skill

            graph = GraphService()
            for skill in Skill.objects.all():
                graph.add_skill_to_graph(skill.name, skill.level)
        except (OperationalError, ProgrammingError):
            pass
