import graphene

from .mutations import Mutation
from .types import Query

schema = graphene.Schema(query=Query, mutation=Mutation)
