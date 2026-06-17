import graphene
from graphene_django import DjangoObjectType

from apps.graph.services import GraphService
from apps.recommendations.engine import RecommendationEngine
from apps.resources.course import CoursesService
from apps.resources.github import GitHubService
from apps.resources.youtube import YouTubeService
from apps.skills.models import Skill, UserSkill
from apps.users.models import User


class UserType(DjangoObjectType):
    class Meta:
        model = User
        exclude = ("password",)


class SkillType(DjangoObjectType):
    class Meta:
        model = Skill


class UserSkillType(DjangoObjectType):
    class Meta:
        model = UserSkill


class GraphNodeType(graphene.ObjectType):
    id = graphene.String()
    name = graphene.String()
    level = graphene.String()


class GraphEdgeType(graphene.ObjectType):
    from_skill = graphene.String(name="from")
    to_skill = graphene.String(name="to")
    type = graphene.String()


class SkillGraphType(graphene.ObjectType):
    nodes = graphene.List(GraphNodeType)
    edges = graphene.List(GraphEdgeType)


class LearningPathType(graphene.ObjectType):
    path = graphene.List(graphene.String)
    distance = graphene.Float()
    weights = graphene.List(graphene.Float)
    levels = graphene.List(graphene.String)


class NextSkillType(graphene.ObjectType):
    skill = graphene.String()
    level = graphene.String()
    reason = graphene.String()


class GitHubRepoType(graphene.ObjectType):
    name = graphene.String()
    url = graphene.String()
    language = graphene.String()
    stars = graphene.Int()
    description = graphene.String()


class YouTubeVideoType(graphene.ObjectType):
    title = graphene.String()
    url = graphene.String()


class CourseType(graphene.ObjectType):
    title = graphene.String()
    url = graphene.String()
    lessons_count = graphene.Int()
    rating = graphene.Float()


class Query(graphene.ObjectType):
    users = graphene.List(UserType)
    skills = graphene.List(SkillType)
    skill_graph = graphene.Field(SkillGraphType)
    next_skills = graphene.List(NextSkillType, user_id=graphene.Int(required=True))
    learning_path = graphene.Field(
        LearningPathType,
        start_skill=graphene.String(required=True),
        end_skill=graphene.String(required=True),
    )
    github_repos = graphene.List(
        GitHubRepoType, skill_name=graphene.String(required=True)
    )
    youtube_videos = graphene.List(
        YouTubeVideoType, skill_name=graphene.String(required=True)
    )
    courses = graphene.List(CourseType, skill_name=graphene.String(required=True))

    def resolve_users(self, info):
        return User.objects.all()

    def resolve_skills(self, info):
        return Skill.objects.all()

    def resolve_skill_graph(self, info):
        payload = GraphService().to_graph_payload()
        nodes = [GraphNodeType(**n) for n in payload["nodes"]]
        edges = [
            GraphEdgeType(from_skill=e["from"], to_skill=e["to"], type=e["type"])
            for e in payload["edges"]
        ]
        return SkillGraphType(nodes=nodes, edges=edges)

    def resolve_next_skills(self, info, user_id):
        user = User.objects.get(id=user_id)
        known = list(user.user_skills.values_list("skill__name", flat=True))
        engine = RecommendationEngine()
        return [NextSkillType(**r) for r in engine.get_next_skills(known)]

    def resolve_learning_path(self, info, start_skill, end_skill):
        engine = RecommendationEngine()
        path = engine.find_learning_path(start_skill, end_skill)
        if not path:
            return None
        return LearningPathType(**path)

    def resolve_github_repos(self, info, skill_name):
        return [GitHubRepoType(**r) for r in GitHubService().search_repos(skill_name)]

    def resolve_youtube_videos(self, info, skill_name):
        return [
            YouTubeVideoType(**v) for v in YouTubeService().search_videos(skill_name)
        ]

    def resolve_courses(self, info, skill_name):
        service = CoursesService()
        courses = service.search_stepik_courses(
            skill_name
        ) + service.search_coursera_courses(skill_name)
        return [CourseType(**c) for c in courses]
