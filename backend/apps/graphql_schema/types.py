import graphene
from graphene_django import DjangoObjectType
from apps.users.models import User
from apps.skills.models import Skill
from apps.recommendations.engine import RecommendationEngine
from apps.resources.github import GitHubService
from apps.resources.youtube import YouTubeService
from apps.resources.stepik import StepikService

class UserType(DjangoObjectType):
    class Meta:
        model = User
        exclude = ('password',)

class SkillType(DjangoObjectType):
    class Meta:
        model = Skill

class GitHubRepoType(graphene.ObjectType):
    name = graphene.String()
    url = graphene.String()
    language = graphene.String()
    stars = graphene.Int()
    description = graphene.String()
    snippet = graphene.String()

class YouTubeVideoType(graphene.ObjectType):
    title = graphene.String()
    url = graphene.String()
    duration = graphene.String()
    views = graphene.Int()
    published_date = graphene.String()

class StepikCourseType(graphene.ObjectType):
    title = graphene.String()
    url = graphene.String()
    lessons_count = graphene.Int()
    rating = graphene.Float()

class Query(graphene.ObjectType):
    users = graphene.List(UserType)
    skills = graphene.List(SkillType)
    next_skills = graphene.List(SkillType, user_id=graphene.Int())
    learning_path = graphene.JSONString(start_skill=graphene.String(), end_skill=graphene.String())
    github_repos = graphene.List(GitHubRepoType, skill_name=graphene.String())
    youtube_videos = graphene.List(YouTubeVideoType, skill_name=graphene.String())
    stepik_courses = graphene.List(StepikCourseType, skill_name=graphene.String())

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
        return {"path": path} if path else {"error": "Путь не найден"}

    def resolve_github_repos(self, info, skill_name):
        service = GitHubService()
        repos = service.search_repos(skill_name)
        return repos

    def resolve_youtube_videos(self, info, skill_name):
        service = YouTubeService()
        videos = service.search_videos(skill_name)
        return videos

    def resolve_stepik_courses(self, info, skill_name):
        service = StepikService()
        courses = service.search_courses(skill_name)
        return courses

class CreateSkill(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        description = graphene.String()
        level = graphene.String()
        tags = graphene.List(graphene.String)

    skill = graphene.Field(SkillType)

    def mutate(self, info, name, description=None, level='beginner', tags=None):
        user = info.context.user
        skill = Skill.objects.create(
            name=name,
            description=description,
            level=level,
            owner=user
        )

        if tags:
            skill.tags.extend(tags)
            skill.save()

        return CreateSkill(skill=skill)

class UpdateSkill(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)
        name = graphene.String()
        description = graphene.String()
        level = graphene.String()
        tags = graphene.List(graphene.String)

    skill = graphene.Field(SkillType)

    def mutate(self, info, id, **kwargs):
        skill = Skill.objects.get(id=id)
        for attr, value in kwargs.items():
            if value is not None:
                setattr(skill, attr, value)
        skill.save()
        return UpdateSkill(skill=skill)

class Mutation(graphene.ObjectType):
    create_skill = CreateSkill.Field()
    update_skill = UpdateSkill.Field()
