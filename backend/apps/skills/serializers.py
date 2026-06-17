from rest_framework import serializers

from .models import Skill, UserSkill


class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = [
            "id",
            "name",
            "description",
            "level",
            "tags",
            "is_verified",
            "created_at",
            "updated_at",
        ]


class UserSkillSerializer(serializers.ModelSerializer):
    """Сериализатор связи пользователь–навык: при чтении возвращает вложенный объект навыка,
    при записи принимает skill_id (PK).
    """

    skill = SkillSerializer(read_only=True)
    skill_id = serializers.PrimaryKeyRelatedField(
        queryset=Skill.objects.all(), source="skill", write_only=True
    )

    class Meta:
        model = UserSkill
        fields = ["id", "skill", "skill_id", "level", "acquired_at"]
