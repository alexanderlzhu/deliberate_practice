#!/usr/bin/env python3
"""Rich CLI for deliberate practice graph database."""

import argparse
import os
import sys
from schema import get_db, init_schema

from rich.console import Console
from rich.table import Table
from rich.tree import Tree
from rich.panel import Panel
from rich.columns import Columns
from rich import box

console = Console()

def node_exists(conn, node_type, key_field, key_value):
    """Check if a node exists."""
    result = conn.execute(
        f"MATCH (n:{node_type} {{{key_field}: $val}}) RETURN count(n)",
        {"val": key_value}
    )
    if result.has_next():
        return result.get_next()[0] > 0
    return False

def add_model(name, model_type, description, file_path=None):
    conn = get_db()
    conn.execute(
        "MERGE (m:Model {name: $name}) SET m.type = $mtype, m.description = $descr, m.file_path = $fpath",
        {"name": name, "mtype": model_type, "descr": description, "fpath": file_path or ""}
    )
    console.print(f"[green]Added model:[/green] {name}")

def add_observation(slug, date, summary, file_path=None):
    conn = get_db()
    conn.execute(
        "MERGE (o:Observation {slug: $slug}) SET o.date = $odate, o.summary = $summ, o.file_path = $fpath",
        {"slug": slug, "odate": date, "summ": summary, "fpath": file_path or ""}
    )
    console.print(f"[green]Added observation:[/green] {slug}")

def add_activity(name):
    conn = get_db()
    conn.execute("MERGE (a:Activity {name: $name})", {"name": name})
    console.print(f"[green]Added activity:[/green] {name}")

def add_concept(name, description=""):
    conn = get_db()
    conn.execute(
        "MERGE (c:Concept {name: $name}) SET c.description = $descr",
        {"name": name, "descr": description}
    )
    console.print(f"[green]Added concept:[/green] {name}")

def add_gap(name, status="open", file_path=None):
    conn = get_db()
    conn.execute(
        "MERGE (g:Gap {name: $name}) SET g.status = $gstatus, g.file_path = $fpath",
        {"name": name, "gstatus": status, "fpath": file_path or ""}
    )
    console.print(f"[green]Added gap:[/green] {name}")

def link(from_type, from_name, rel_type, to_type, to_name, **props):
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
    console.print(rf"[blue]Linked:[/blue] ({from_name}) -\[{rel_type}]-> ({to_name})")

def link_observation(obs_slug, rel_type, model_name, **props):
    conn = get_db()
    q = f"""
        MATCH (o:Observation {{slug: $slug}}), (m:Model {{name: $model_name}})
        MERGE (o)-[r:{rel_type}]->(m)
    """
    params = {"slug": obs_slug, "model_name": model_name}
    conn.execute(q, params)
    console.print(rf"[blue]Linked Obs:[/blue] ({obs_slug}) -\[{rel_type}]-> ({model_name})")

def link_applies(model_name, activity_name):
    conn = get_db()
    conn.execute(
        "MATCH (m:Model {name: $mname}), (a:Activity {name: $aname}) MERGE (m)-[:APPLIES_TO]->(a)",
        {"mname": model_name, "aname": activity_name}
    )
    console.print(rf"[blue]Linked:[/blue] ({model_name}) -\[APPLIES_TO]-> ({activity_name})")

def visualize(target=None):
    """Render a rich dashboard of the investigative graph."""
    conn = get_db()
    
    # 1. Title
    console.print(Panel.fit("[bold cyan]INVESTIGATIVE SYSTEMS DASHBOARD[/bold cyan]", box=box.DOUBLE))

    # 2. Stats
    stats_table = Table(box=box.SIMPLE)
    stats_table.add_column("Type", style="bold")
    stats_table.add_column("Count", justify="right")
    
    for ntype in ["Model", "Observation", "Activity", "Gap", "Concept"]:
        res = conn.execute(f"MATCH (n:{ntype}) RETURN count(n)")
        count = res.get_next()[0] if res.has_next() else 0
        stats_table.add_row(ntype, str(count))
    
    # 3. Gap Status Table
    gap_table = Table(title="Gap Status Board", box=box.ROUNDED)
    gap_table.add_column("Status", width=3)
    gap_table.add_column("Gap Name", style="bold yellow")
    gap_table.add_column("Current State", justify="center")
    
    res = conn.execute("MATCH (g:Gap) RETURN g.name, g.status")
    while res.has_next():
        name, status = res.get_next()
        color = "green" if status == "resolved" else "red"
        sym = "✓" if status == "resolved" else "!"
        gap_table.add_row(f"[{color}]{sym}[/{color}]", name, f"[{color}]{status}[/{color}]")

    console.print(Columns([stats_table, gap_table]))

    # 4. Master Model Tree
    res = conn.execute("MATCH (m:Model {name: 'Dynamical Systems'}) RETURN m.name, m.description")
    if res.has_next():
        name, desc = res.get_next()
        tree = Tree(f"\n[bold magenta]{name}[/bold magenta] [italic white]({desc})[/italic white]")
        
        # Incoming relations to Master
        res_in = conn.execute(
            "MATCH (n)-[r]->(m:Model {name: 'Dynamical Systems'}) RETURN labels(n)[0], coalesce(n.name, n.slug), label(r)"
        )
        while res_in.has_next():
            ntype, nname, rtype = res_in.get_next()
            color = "cyan" if ntype == "Observation" else "yellow"
            tree.add(f"[dim]<-({rtype})-[/dim] [{color}]{nname}[/{color}] ({ntype})")
            
        # Outgoing relations from Master
        res_out = conn.execute(
            "MATCH (m:Model {name: 'Dynamical Systems'})-[r]->(target) RETURN label(r), labels(target)[0], target.name"
        )
        while res_out.has_next():
            rtype, ttype, tname = res_out.get_next()
            tree.add(f"[dim]-({rtype})->[/dim] [green]{tname}[/green] ({ttype})")
            
        console.print(tree)

    # 5. Activity Mapping (Chess)
    res = conn.execute("MATCH (m:Model)-[:APPLIES_TO]->(a:Activity {name: 'Chess'}) RETURN m.name")
    models = []
    while res.has_next():
        models.append(res.get_next()[0])
    
    if models:
        console.print(f"\n[bold blue]Activity: Chess[/bold blue]")
        console.print(f"  [italic]Active Models:[/italic] {', '.join(sorted(models))}")

    console.print("\n")

def query(cypher):
    conn = get_db()
    result = conn.execute(cypher)
    table = Table(box=box.MINIMAL)
    
    first = True
    while result.has_next():
        row = result.get_next()
        if first:
            for i in range(len(row)):
                table.add_column(f"Col {i}")
            first = False
        table.add_row(*[str(x) for x in row])
    console.print(table)

def list_nodes(node_type):
    conn = get_db()
    table = Table(title=f"{node_type}s", box=box.SIMPLE)
    
    if node_type == "Observation":
        table.add_column("Slug", style="bold")
        table.add_column("Summary")
        res = conn.execute(f"MATCH (n:{node_type}) RETURN n.slug, n.summary")
    elif node_type == "Gap":
        table.add_column("Name", style="bold")
        table.add_column("Status")
        res = conn.execute(f"MATCH (n:{node_type}) RETURN n.name, n.status")
    elif node_type == "Activity":
        table.add_column("Name", style="bold")
        res = conn.execute(f"MATCH (n:{node_type}) RETURN n.name")
    else:
        table.add_column("Name", style="bold")
        table.add_column("Description")
        res = conn.execute(f"MATCH (n:{node_type}) RETURN n.name, coalesce(n.description, '')")
        
    while res.has_next():
        table.add_row(*[str(x) for x in res.get_next()])
    console.print(table)

def main():
    parser = argparse.ArgumentParser(description="Investigative CLI")
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

    p = subparsers.add_parser("list")
    p.add_argument("type", choices=["Model", "Observation", "Activity", "Gap", "Concept"])

    p = subparsers.add_parser("viz")
    p.add_argument("--target", help="Focus on specific node")

    p = subparsers.add_parser("query")
    p.add_argument("cypher")

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
        link_observation(args.obs_slug, args.rel_type, args.model_name)
    elif args.command == "list":
        list_nodes(args.type)
    elif args.command == "viz":
        visualize(args.target)
    elif args.command == "query":
        query(args.cypher)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
