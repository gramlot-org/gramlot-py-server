"""Local development commands for the Flask adapter."""
from pathlib import Path
import click


@click.group(invoke_without_command=True)
@click.pass_context
def main(ctx):
    """Start Microblog with the Gramlot integration demo by default."""
    if ctx.invoked_subcommand is None:
        ctx.invoke(demo)


@main.command()
@click.option("--data-dir", type=click.Path(path_type=Path),
              default=lambda: Path(click.get_app_dir("gramlot-flask")) / "microblog")
@click.option("--port", type=click.IntRange(1, 65535), default=8073, show_default=True)
def demo(data_dir, port):
    """Run the local Microblog demo, using a separate persistent SQLite database."""
    try:
        from .demo import create_demo, close_demo
        app = create_demo(data_dir)
    except ModuleNotFoundError as error:
        raise click.ClickException("Install the demo dependencies: pip install 'gramlot-flask[demo]'"
                                   f" (missing {error.name})") from error
    click.echo(f"Microblog: http://127.0.0.1:{port}/")
    click.echo(f"Gramlot:   http://127.0.0.1:{port}/gramlot/community/")
    click.echo("Demo login: demo / gramlot-demo")
    click.echo(f"Demo database: {Path(data_dir).expanduser().resolve() / 'microblog.sqlite'}")
    try:
        app.run(host="127.0.0.1", port=port, debug=False, use_reloader=False)
    finally:
        close_demo(app)


@main.command()
@click.argument("directory", type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.option("--port", type=click.IntRange(1, 65535), default=8073, show_default=True)
def serve(directory, port):
    """Serve a directory containing pages/ without Microblog or a database."""
    from flask import Flask
    from .application import mount_gramlot
    app = Flask(__name__)
    mount_gramlot(app, directory)
    app.run(host="127.0.0.1", port=port, debug=False, use_reloader=False)
