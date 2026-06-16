import graphene
from graphene_django import DjangoObjectType
from apps.skills.models import Skill
from apps.graph.services import GraphService
from apps.users.models import User
from typing import Optional

class AddSkillDependency(graphene.Mutation):
    class Arguments:
        skill1 = graphene.String(required=True)
        skill2 = graphene.String(required=True)
        relation_type = graphene.String(default_value="DEPENDS_ON")

    success = graphene.Boolean()
    message = graphene.String()

    def mutate(self, info, skill1: str, skill2: str, relation_type: str):
        graph = GraphService()
        try:
            success = graph.add_dependency(skill1, skill2, relation_type)
            return AddSkillDependency(success=success, message="Зависимость добавлена")
        except Exception as e:
            return AddSkillDependency(success=False, message=str(e))

class UpdateSkillLevel(graphene.Mutation):
    class Arguments:
        skill_name = graphene.String(required=True)
        new_level = graphene.String(required=True)

    success = graphene.Boolean()
    message = graphene.String()

    def mutate(self, info, skill_name: str, new_level: str):
        try:
            skill = Skill.objects.get(name=skill_name)
            skill.level = new_level
            skill.save()

            # Обновляем граф Neo4j
            graph = GraphService()
            graph.add_skill_to_graph(skill_name, new_level)

            return UpdateSkillLevel(success=True, message="Уровень обновлён")
        except Skill.DoesNotExist:
            return UpdateSkillLearningPath(success=False, message="Навык не найден")
        except Exception as e:
            return UpdateSkillLevel(success=False, message=str(e))

class UpdateSkillLearningPath(graphene.Mutation):
    class Arguments:
        skill_name = graphene.String(required=True)
        level = graphene.String(default_value="beginner")
        dependencies = graphene.List(graphene.String)

    success = graphene.Boolean()
    message = graphene.String()
    path = graphene.JSONString()

    def mutate(self, info, skill_name: str, level: str, dependencies: Optional[List[str]]):
        try:
            skill, created = Skill.objects.get_or_create(name=skill_name, defaults={
                "owner": info.context.user,
                "level": level
            })

            if dependencies:
                graph = GraphService()
                for dep in dependencies:
                    graph.add_dependency(skill_name, dep, "DEPENDS_ON")

            # Находим рекомендуемый путь для обучения
            if level != "beginner":
                path = graph.find_shortest_path("beginner", skill_name)
                if path:
                    return UpdateSkillLearningPath(
                        success=True,
                        message="Навык обновлён и путь найден",
                        path=json.dumps(path)
                    )

            return UpdateSkillLearningPath(
                success=True,
                message="Навык обновлён"
            )
        except Exception as e:
            return UpdateSkillLearningPath(success=False, message=str(e))

class Mutation(graphene.ObjectType):
    add_skill_dependency = AddSkillDependency.Field()
    update_skill_level = UpdateSkillLevel.Field()
    update_skill_learning_path = UpdateSkillLearningPath.Field()
