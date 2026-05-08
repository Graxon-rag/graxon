class Neo4jHelper:
    def __init__(self):
        pass

    @staticmethod
    def get_unique_constraint_string(node: str, constraint_string: str, property_name: str = "id") -> str:
        return f"""
            CREATE CONSTRAINT {constraint_string} IF NOT EXISTS
            FOR (n:{node})
            REQUIRE n.{property_name} IS UNIQUE
        """
