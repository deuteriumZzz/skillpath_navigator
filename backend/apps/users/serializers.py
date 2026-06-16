from rest_framework import serializers
from django.contrib.auth import get_user_model
from apps.skills.models import Skill

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    skills = serializers.PrimaryKeyRelatedField(
        many=True,
        read_only=True,
        source='skill_set'
    )

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'avatar', 'bio', 'skills']
