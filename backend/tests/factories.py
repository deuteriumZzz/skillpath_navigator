import factory
from django.contrib.auth import get_user_model
from factory.django import DjangoModelFactory

from apps.skills.models import Skill, UserSkill

User = get_user_model()


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.LazyAttribute(lambda o: f"{o.username}@example.com")
    password = factory.PostGenerationMethodCall("set_password", "testpass123")


class SkillFactory(DjangoModelFactory):
    class Meta:
        model = Skill

    name = factory.Sequence(lambda n: f"Skill {n}")
    level = "beginner"
    description = ""


class UserSkillFactory(DjangoModelFactory):
    class Meta:
        model = UserSkill

    user = factory.SubFactory(UserFactory)
    skill = factory.SubFactory(SkillFactory)
    level = "beginner"
