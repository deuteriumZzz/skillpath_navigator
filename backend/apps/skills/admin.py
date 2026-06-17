from django.contrib import admin

from .models import Skill, UserSkill


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ("name", "level", "is_verified", "created_at")
    list_filter = ("level", "is_verified")
    search_fields = ("name", "description")
    ordering = ("name",)
    list_editable = ("is_verified",)


@admin.register(UserSkill)
class UserSkillAdmin(admin.ModelAdmin):
    list_display = ("user", "skill", "level", "acquired_at")
    list_filter = ("level",)
    search_fields = ("user__username", "skill__name")
    raw_id_fields = ("user", "skill")
