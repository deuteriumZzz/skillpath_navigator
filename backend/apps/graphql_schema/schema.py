import graphene
from graphene_django import DjangoObjectType
from .types import Query, Mutation

class SkillPathSchema(graphene.Schema):
    query = Query
    mutation = Mutation
