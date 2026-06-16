from neo4j import GraphDatabase
from django.conf import settings
from functools import lru_cache

@lru_cache
def get_neo4j_driver():
    return GraphDatabase.driver(
        settings.NEO4J_URI,
        auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
    )

def execute_query(query, parameters=None):
    driver = get_neo4j_driver()
    try:
        with driver.session() as session:
            result = session.run(query, parameters or {})
            return [dict(record) for record in result]
    finally:
        driver.close()

def add_skill_to_graph(skill_name, skill_level):
    query = """
    MERGE (s:Skill {name: $name})
    SET s.level = $level
    """
    execute_query(query, {'name': skill_name, 'level': skill_level})

def add_dependency(from_skill, to_skill, strength=0.9):
    query = """
    MATCH (from:Skill {name: $from}), (to:Skill {name: $to})
    MERGE (from)-[r:DEPENDS_ON {strength: $strength}]->(to)
    """
    execute_query(query, {
        'from': from_skill,
        'to': to_skill,
        'strength': strength
    })

def get_skill_graph(limit=100):
    query = """
    MATCH (s:Skill)-[r:DEPENDS_ON]->(other)
    RETURN s.name AS from, other.name AS to, r.strength AS strength
    LIMIT $limit
    """
    return execute_query(query, {'limit': limit})
