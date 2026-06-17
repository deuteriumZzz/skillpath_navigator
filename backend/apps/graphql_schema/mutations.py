import graphene

from apps.graph.services import GraphService
from apps.progress.models import UserSkillProgress
from apps.progress.services import broadcast_progress_update
from apps.recommendations.services import ingest_skills_from_text
from apps.skills.models import Skill

from .types import SkillType, UserSkillType


class CreateSkill(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        description = graphene.String()
        level = graphene.String(default_value="beginner")
        tags = graphene.List(graphene.String)

    skill = graphene.Field(SkillType)

    def mutate(self, info, name, description="", level="beginner", tags=None):
        skill = Skill.objects.create(
            name=name,
            description=description,
            level=level,
            tags=tags or [],
        )
        return CreateSkill(skill=skill)


class AddSkillDependency(graphene.Mutation):
    class Arguments:
        skill = graphene.String(required=True)
        depends_on = graphene.String(required=True)
        relation_type = graphene.String(default_value="DEPENDS_ON")

    success = graphene.Boolean()
    message = graphene.String()

    def mutate(self, info, skill, depends_on, relation_type):
        try:
            GraphService().add_dependency(skill, depends_on, relation_type)
            return AddSkillDependency(success=True, message="Зависимость добавлена")
        except ValueError as e:
            return AddSkillDependency(success=False, message=str(e))


class IngestSkillsFromText(graphene.Mutation):
    class Arguments:
        text = graphene.String(required=True)

    skills = graphene.List(UserSkillType)

    def mutate(self, info, text):
        user = info.context.user
        if not user or not user.is_authenticated:
            raise Exception("Требуется аутентификация")
        created = ingest_skills_from_text(user, text)
        return IngestSkillsFromText(skills=created)


class UpdateProgress(graphene.Mutation):
    class Arguments:
        skill_name = graphene.String(required=True)
        completion_percent = graphene.Int(required=True)

    success = graphene.Boolean()
    completion_percent = graphene.Int()

    def mutate(self, info, skill_name, completion_percent):
        user = info.context.user
        if not user or not user.is_authenticated:
            raise Exception("Требуется аутентификация")
        skill = Skill.objects.get(name=skill_name)
        progress, _ = UserSkillProgress.objects.update_or_create(
            user=user, skill=skill, defaults={"completion_percent": completion_percent}
        )
        broadcast_progress_update(user.id, skill.name, progress.completion_percent)
        return UpdateProgress(
            success=True, completion_percent=progress.completion_percent
        )


class Mutation(graphene.ObjectType):
    create_skill = CreateSkill.Field()
    add_skill_dependency = AddSkillDependency.Field()
    ingest_skills_from_text = IngestSkillsFromText.Field()
    update_progress = UpdateProgress.Field()
