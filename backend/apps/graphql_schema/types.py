import graphene
from graphene_django import DjangoObjectType
from apps.users.models import User
from apps.skills.models import Skill
from apps.recommendations.engine import RecommendationEngine
from apps.resources.github import GitHubService

class UserType(DjangoObjectType):
    class Meta:
        model = User

class SkillType(DjangoObjectType):
    class Meta:
        model = Skill

class Query(graphene.ObjectType):
    users = graphene.List(UserType)
    skills = graphene.List(SkillType)
    next_skills = graphene.List(SkillType, user_id=graphene.Int())
    learning_path = graphene.JSONString(start_skill=graphene.String(), end_skill=graphene.String())
    github_repos = graphene.JSONString(skill_name=graphene.String())

    def resolve_users(self, info):
        return User.objects.all()

    def resolve_skills(self, info):
        return Skill.objects.all()

    def resolve_next_skills(self, info, user_id):
        if user_id:
            user = User.objects.get(id=user_id)
            engine = RecommendationEngine()
            return engine.get_next_skills(user.skills.all())
        return []

    def resolve_learning_path(self, info, start_skill, end_skill):
        engine = RecommendationEngine()
        path = engine.find_learning_path(start_skill, end_skill)
        return path if path else "Путь не найден"

    def resolve_github_repos(self, info, skill_name):
        service = GitHubService()
        repos = service.search_repos(skill_name)
        return repos

class CreateSkill(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        description = graphene.String()

    skill = graphene.Field(SkillType)

    def mutate(self, info, name, description):
        user = info.context.user
        skill = Skill(name=name, description=description, owner=user)
        skill.save()
        return CreateSkill(skill=skill)

class Mutation(graphene.ObjectType):
    create_skill = CreateSkill.Field()
