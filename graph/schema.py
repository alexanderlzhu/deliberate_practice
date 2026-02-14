#!/usr/bin/env python3
"""Initialize Kuzu graph database schema for deliberate practice."""

import kuzu
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "data")


def get_db():
    """Get database connection."""
    db = kuzu.Database(DB_PATH)
    return kuzu.Connection(db)


def init_schema():
    """Create node and relationship tables."""
    conn = get_db()

    # Node tables
    conn.execute("""
        CREATE NODE TABLE IF NOT EXISTS Model(
            name STRING,
            type STRING,
            description STRING,
            file_path STRING,
            PRIMARY KEY(name)
        )
    """)

    conn.execute("""
        CREATE NODE TABLE IF NOT EXISTS Observation(
            slug STRING,
            date STRING,
            summary STRING,
            file_path STRING,
            PRIMARY KEY(slug)
        )
    """)

    conn.execute("""
        CREATE NODE TABLE IF NOT EXISTS Gap(
            name STRING,
            status STRING,
            file_path STRING,
            PRIMARY KEY(name)
        )
    """)

    conn.execute("""
        CREATE NODE TABLE IF NOT EXISTS Activity(
            name STRING,
            PRIMARY KEY(name)
        )
    """)

    conn.execute("""
        CREATE NODE TABLE IF NOT EXISTS Concept(
            name STRING,
            description STRING,
            PRIMARY KEY(name)
        )
    """)

    # Relationship tables
    conn.execute("""
        CREATE REL TABLE IF NOT EXISTS SUPPORTS(
            FROM Observation TO Model,
            strength STRING
        )
    """)

    conn.execute("""
        CREATE REL TABLE IF NOT EXISTS CONTRADICTS(
            FROM Observation TO Model,
            notes STRING
        )
    """)

    conn.execute("""
        CREATE REL TABLE IF NOT EXISTS CAUSES(
            FROM Model TO Model,
            mechanism STRING
        )
    """)

    conn.execute("""
        CREATE REL TABLE IF NOT EXISTS RELATED_TO(
            FROM Model TO Model,
            relationship STRING
        )
    """)

    conn.execute("""
        CREATE REL TABLE IF NOT EXISTS ABOUT(
            FROM Observation TO Activity
        )
    """)

    conn.execute("""
        CREATE REL TABLE IF NOT EXISTS APPLIES_TO(
            FROM Model TO Activity
        )
    """)

    conn.execute("""
        CREATE REL TABLE IF NOT EXISTS INVOLVES(
            FROM Model TO Concept
        )
    """)

    conn.execute("""
        CREATE REL TABLE IF NOT EXISTS RESOLVED_BY(
            FROM Gap TO Model
        )
    """)

    conn.execute("""
        CREATE REL TABLE IF NOT EXISTS UNEXPLAINED_BY(
            FROM Gap TO Model,
            reason STRING
        )
    """)

    print("Schema initialized successfully.")


if __name__ == "__main__":
    init_schema()
