from django.views.generic import ListView, DetailView
from django.shortcuts import get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Skill
from apps.graph.services import GraphService
from apps.recommendations.engine import RecommendationEngine
import json

class SkillListView(LoginRequiredMixin, ListView):
    model = Skill
    template_name = "skills/skill_list.html"
    context_object_name = "skills"
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset().filter(owner=self.request.user)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        engine = RecommendationEngine()
        context["recommended_skills"] = engine.get_next_skills(self.request.user.skills.all())
        return context

class SkillDetailView(LoginRequiredMixin, DetailView):
    model = Skill
    template_name = "skills/skill_detail.html"
    context_object_name = "skill"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        skill = self.object
        graph = GraphService()

        # Получаем зависимости навыка
        dependencies = graph.get_skill_dependencies(skill.name)
        context["dependencies"] = dependencies

        # Ищем возможные пути учёбы от базовых навыков к данному
        context["learning_paths"] = []
        for level in ["beginner", "intermediate"]:
            path = graph.find_shortest_path(level, skill.name)
            if path:
                context["learning_paths"].append({
                    "from": level,
                    "path": path["path"],
                    "levels": path["levels"],
                    "distance": path["distance"]
                })

        return context
