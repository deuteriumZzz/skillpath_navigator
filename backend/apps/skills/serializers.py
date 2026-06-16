from rest_framework import serializers
from .models import Skill, SkillTag

class SkillTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = SkillTag
        fields = ['id', 'name']

class SkillSerializer(serializers.ModelSerializer):
    owner = serializers.ReadOnlyField(source='owner.username')
    tags = SkillTagSerializer(many=True, read_only=True)

    class Meta:
        model = Skill
        fields = ['id', 'name', 'description', 'level', 'owner', 'created_at', 'tags']
