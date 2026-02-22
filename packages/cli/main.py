"""
Secrin CLI entry point.

  secrin init --repo <url>         Clone, parse, analyse, generate wiki.
  secrin ask "<question>"          Ask a question answered from the wiki.
  secrin graph build --path <dir>  Build the Neo4j code knowledge graph.
"""
import typer

from packages.cli.commands.init import init
from packages.cli.commands.ask import ask
from packages.cli.commands.graph import graph_app

app = typer.Typer(
    name="secrin",
    help="Your team's living software encyclopedia.",
    add_completion=False,
)

app.command("init")(init)
app.command("ask")(ask)
app.add_typer(graph_app, name="graph")

if __name__ == "__main__":
    app()
