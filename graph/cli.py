#!/usr/bin/env python3
"""CLI for deliberate practice graph database."""

import argparse
import os
import sys
from schema import get_db, init_schema

def node_exists(conn, node_type, key_field, key_value):
    """Check if a node exists. Returns True/False."""
    result = conn.execute(
        f"MATCH (n:{node_type} {{{key_field}: $val}}) RETURN count(n)",
        {"val": key_value}
    )
    if result.has_next():
        return result.get_next()[0] > 0
    return False

def add_model(name, model_type, description, file_path=None):
    """Add a model node."""
    conn = get_db()
    conn.execute(
        "MERGE (m:Model {name: $name}) SET m.type = $mtype, m.description = $descr, m.file_path = $fpath",
        {"name": name, "mtype": model_type, "descr": description, "fpath": file_path or ""}
    )
    print(f"Added model: {name}")

def add_observation(slug, date, summary, file_path=None):
    """Add an observation node."""
    conn = get_db()
    conn.execute(
        "MERGE (o:Observation {slug: $slug}) SET o.date = $odate, o.summary = $summ, o.file_path = $fpath",
        {"slug": slug, "odate": date, "summ": summary, "fpath": file_path or ""}
    )
    print(f"Added observation: {slug}")

def add_activity(name):
    """Add an activity node."""
    conn = get_db()
    conn.execute("MERGE (a:Activity {name: $name})", {"name": name})
    print(f"Added activity: {name}")

def add_gap(name, status="open", file_path=None):
    """Add a gap node."""
    conn = get_db()
    conn.execute(
        "MERGE (g:Gap {name: $name}) SET g.status = $gstatus, g.file_path = $fpath",
        {"name": name, "gstatus": status, "fpath": file_path or ""}
    )
    print(f"Added gap: {name}")

def add_concept(name, description=""):
    """Add a concept node."""
    conn = get_db()
    conn.execute(
        "MERGE (c:Concept {name: $name}) SET c.description = $descr",
        {"name": name, "descr": description}
    )
    print(f"Added concept: {name}")

def link(from_type, from_name, rel_type, to_type, to_name, **props):
    """Create a relationship between nodes."""
    conn = get_db()
    from_key = "slug" if from_type == "Observation" else "name"
    to_key = "slug" if to_type == "Observation" else "name"
    
    prop_str = ", ".join(f"r.{k} = ${k}" for k in props.keys()) if props else ""
    set_clause = f"SET {prop_str}" if prop_str else ""

    q = f"""
        MATCH (a:{from_type} {{{from_key}: $from_name}}), (b:{to_type} {{{to_key}: $to_name}})
        MERGE (a)-[r:{rel_type}]->(b)
        {set_clause}
    """
    params = {"from_name": from_name, "to_name": to_name, **props}
    conn.execute(q, params)
    print(f"Linked: ({from_name})-[{rel_type}]->({to_name})")

def show_model(name):
    """Show a model and its relationships."""
    conn = get_db()
    print(f"\n=== Model: {name} ===\n")
    result = conn.execute(
        "MATCH (m:Model {name: $name}) RETURN m.type, m.description, m.file_path",
        {"name": name}
    )
    if result.has_next():
        row = result.get_next()
        print(f"Type: {row[0]}")
        print(f"Description: {row[1]}")
        print(f"File: {row[2]}")

    print("\nRelationships:")
    result = conn.execute(
        "MATCH (m:Model {name: $name})-[r]->(target) RETURN type(r), labels(target)[0], target.name",
        {"name": name}
    )
    while result.has_next():
        row = result.get_next()
        print(f"  -[{row[0]}]-> {row[1]}({row[2]})")

def link_observation(obs_slug, rel_type, model_name, **props):
    """Link observation to model."""
    conn = get_db()
    obs_ok = node_exists(conn, "Observation", "slug", obs_slug)
    model_ok = node_exists(conn, "Model", "name", model_name)
    if not obs_ok or not model_ok:
        print(f"Error: Node(s) not found. Obs: {obs_ok}, Model: {model_ok}")
        return

    prop_str = ", ".join(f"r.{k} = ${k}" for k in props.keys()) if props else ""
    set_clause = f"SET {prop_str}" if prop_str else ""

    q = f"""
        MATCH (o:Observation {{slug: $slug}}), (m:Model {{name: $model_name}})
        MERGE (o)-[r:{rel_type}]->(m)
        {set_clause}
    """
    params = {"slug": obs_slug, "model_name": model_name, **props}
    conn.execute(q, params)
    print(f"Linked: ({obs_slug})-[{rel_type}]->({model_name})")

def link_applies(model_name, activity_name):
    """Link model to activity."""
    conn = get_db()
    model_ok = node_exists(conn, "Model", "name", model_name)
    activity_ok = node_exists(conn, "Activity", "name", activity_name)
    if not model_ok or not activity_ok:
        print(f"Error: Node(s) not found. Model: {model_ok}, Activity: {activity_ok}")
        return

    conn.execute(
        "MATCH (m:Model {name: $mname}), (a:Activity {name: $aname}) MERGE (m)-[:APPLIES_TO]->(a)",
        {"mname": model_name, "aname": activity_name}
    )
    print(f"Linked: ({model_name})-[APPLIES_TO]->({activity_name})")

def query(cypher):
    """Run arbitrary Cypher query."""
    conn = get_db()
    result = conn.execute(cypher)
    while result.has_next():
        print(result.get_next())

def list_nodes(node_type):
    """List all nodes of a type."""
    conn = get_db()
    if node_type == "Observation":
        result = conn.execute(f"MATCH (n:{node_type}) RETURN n.slug, n.summary")
    elif node_type == "Activity":
        result = conn.execute(f"MATCH (n:{node_type}) RETURN n.name, ''")
    else:
        result = conn.execute(f"MATCH (n:{node_type}) RETURN n.name, n.description")
    print(f"\n{node_type}s:")
    while result.has_next():
        row = result.get_next()
        print(f"  {row[0]}: {row[1] or ''}")

def main():
    parser = argparse.ArgumentParser(description="Deliberate Practice Graph CLI")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("init")
    
    p = subparsers.add_parser("add-model")
    p.add_argument("name")
    p.add_argument("--type", default="mental")
    p.add_argument("--description", default="")
    p.add_argument("--file", default=None)

    p = subparsers.add_parser("add-obs")
    p.add_argument("slug")
    p.add_argument("--date", required=True)
    p.add_argument("--summary", default="")
    p.add_argument("--file", default=None)

    p = subparsers.add_parser("add-activity")
    p.add_argument("name")

    p = subparsers.add_parser("add-concept")
    p.add_argument("name")
    p.add_argument("--description", default="")

    p = subparsers.add_parser("add-gap")
    p.add_argument("name")
    p.add_argument("--status", default="open")
    p.add_argument("--file", default=None)

    p = subparsers.add_parser("link")
    p.add_argument("from_type")
    p.add_argument("from_name")
    p.add_argument("rel_type")
    p.add_argument("to_type")
    p.add_argument("to_name")

    p = subparsers.add_parser("link-obs")
    p.add_argument("obs_slug")
    p.add_argument("rel_type", choices=["SUPPORTS", "CONTRADICTS"])
    p.add_argument("model_name")
    p.add_argument("--strength", default="moderate")

    p = subparsers.add_parser("link-applies")
    p.add_argument("model_name")
    p.add_argument("activity_name")

    p = subparsers.add_parser("list")
    p.add_argument("type", choices=["Model", "Observation", "Activity", "Gap", "Concept"])

    p = subparsers.add_parser("query")
    p.add_argument("cypher")

    p = subparsers.add_parser("show")
    p.add_argument("name")

    args = parser.parse_args()

    if args.command == "init":
        init_schema()
    elif args.command == "add-model":
        add_model(args.name, args.type, args.description, args.file)
    elif args.command == "add-obs":
        add_observation(args.slug, args.date, args.summary, args.file)
    elif args.command == "add-activity":
        add_activity(args.name)
    elif args.command == "add-concept":
        add_concept(args.name, args.description)
    elif args.command == "add-gap":
        add_gap(args.name, args.status, args.file)
    elif args.command == "link":
        link(args.from_type, args.from_name, args.rel_type, args.to_type, args.to_name)
    elif args.command == "link-obs":
        link_observation(args.obs_slug, args.rel_type, args.model_name, strength=args.strength)
    elif args.command == "link-applies":
        link_applies(args.model_name, args.activity_name)
    elif args.command == "list":
        list_nodes(args.type)
    elif args.command == "query":
        query(args.cypher)
    elif args.command == "show":
        show_model(args.name)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
