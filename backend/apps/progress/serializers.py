from rest_framework import serializers

from apps.skills.models import Skill

from .models import UserSkillProgress


class UserSkillProgressSerializer(serializers.ModelSerializer):
    skill = serializers.SlugRelatedField(slug_field='name', read_only=True)

    class Meta:
        model = UserSkillProgress
        fields = ['id', 'skill', 'completion_percent', 'updated_at']


class ProgressUpdateSerializer(serializers.Serializer):
    skill_id = serializers.PrimaryKeyRelatedField(queryset=Skill.objects.all())
    completion_percent = serializers.IntegerField(min_value=0, max_value=100)
