"""
Secrin CLI entry point.

  secrin init --repo <url>   Clone, parse, analyse, generate wiki.
  secrin ask "<question>"    Ask a question answered from the wiki.
"""
import typer

from packages.cli.commands.init import init
from packages.cli.commands.ask import ask

app = typer.Typer(
    name="secrin",
    help="Your team's living software encyclopedia.",
    add_completion=False,
)

app.command("init")(init)
app.command("ask")(ask)

if __name__ == "__main__":
    app()
