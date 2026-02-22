"""
Secrin CLI entry point.

  secrin init --repo <url>     Clone, parse, analyse, generate wiki.
  secrin ask "<question>"      Ask a question answered from the wiki.
  secrin graph build --repo … Build the Neo4j code knowledge graph.
  secrin analyze               Summarize graph nodes + store embeddings.
  secrin search "<query>"      Hybrid vector + graph search over the graph.
  secrin domains               Extract business domain entities from summaries.
  secrin generate              Generate docs/wiki/ Markdown from Neo4j.
  secrin post-commit           Incremental graph + wiki update (git hook).
  secrin install-hooks         Install .git/hooks/post-commit.
"""
import typer

from packages.cli.commands.init import init
from packages.cli.commands.ask import ask
from packages.cli.commands.graph import graph_app
from packages.cli.commands.analyze import analyze_app
from packages.cli.commands.search import search
from packages.cli.commands.domains import domains_app
from packages.cli.commands.generate import generate
from packages.cli.commands.hooks import post_commit, install_hooks

app = typer.Typer(
    name="secrin",
    help="Your team's living software encyclopedia.",
    add_completion=False,
)

app.command("init")(init)
app.command("ask")(ask)
app.add_typer(graph_app,    name="graph")
app.add_typer(analyze_app,  name="analyze")
app.command("search")(search)
app.add_typer(domains_app,  name="domains")
app.command("generate")(generate)
app.command("post-commit")(post_commit)
app.command("install-hooks")(install_hooks)

if __name__ == "__main__":
    app()
