from django.db import models  # noqa: F401

# Граф навыков хранится в Neo4j/networkx (см. apps.graph.backends, apps.graph.services),
# а не в реляционной БД — поэтому ORM-моделей в этом приложении нет.
