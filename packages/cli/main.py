"""
Secrin CLI entry point.
"""
import typer

app = typer.Typer(
    name="secrin",
    help="Your team's living software encyclopedia.",
    add_completion=False,
)


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context) -> None:
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())


if __name__ == "__main__":
    app()
