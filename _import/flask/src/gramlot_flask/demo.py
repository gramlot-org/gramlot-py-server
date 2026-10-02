"""Microblog demo assembly. The upstream app and its models remain unchanged."""
from datetime import datetime, timedelta, timezone
from pathlib import Path
import secrets
import sys


def create_demo(data_dir):
    """Create a local demo with its own SQLite file; seed only an empty database."""
    vendor = Path(__file__).parent / "_vendor/microblog"
    loaded = sys.modules.get("app")
    if loaded and not Path(loaded.__file__).is_relative_to(vendor):
        raise RuntimeError("Microblog requires its own process: module 'app' is already in use")
    if str(vendor) not in sys.path:
        sys.path.insert(0, str(vendor))
    from config import Config
    from app import create_app, db
    from app.models import User, Post, Message
    from flask import abort, redirect, request, url_for
    from flask_login import current_user
    from gramlot.contrib.sqlalchemy import SqliteDbHandler, TableConfig
    from jinja2 import ChoiceLoader, DictLoader
    import sqlalchemy as sa
    from .application import mount_gramlot

    data_dir = Path(data_dir).expanduser().resolve()
    data_dir.mkdir(parents=True, exist_ok=True)
    database = data_dir / "microblog.sqlite"

    class DemoConfig(Config):
        SECRET_KEY = secrets.token_hex(32)
        SQLALCHEMY_DATABASE_URI = "sqlite:///" + str(database)
        SQLALCHEMY_TRACK_MODIFICATIONS = False
        LOG_TO_STDOUT = True
        MAIL_SERVER = None
        MAIL_SUPPRESS_SEND = True
        ELASTICSEARCH_URL = None
        MS_TRANSLATOR_KEY = None
        SERVER_NAME = None

    app = create_app(DemoConfig)
    app.config["MAX_CONTENT_LENGTH"] = 1024 * 1024
    with app.app_context():
        db.create_all()
        if db.session.scalar(sa.select(sa.func.count()).select_from(User)) == 0:
            users = []
            names = ["demo", "alice", "bruno", "carla", "david", "elena"]
            topics = ["Python interfaces", "Flask applications", "Open source",
                      "Data exploration", "Design systems", "Community projects"]
            for name, topic in zip(names, topics):
                user = User(username=name, email=f"{name}@example.test",
                            about_me=f"Exploring {topic.lower()} with the Microblog community.")
                user.set_password("gramlot-demo")
                users.append(user)
                db.session.add(user)
            db.session.flush()
            for index, user in enumerate(users):
                user.follow(users[(index + 1) % len(users)])
                user.follow(users[(index + 2) % len(users)])
                for number in range(4):
                    db.session.add(Post(author=user, body=(
                        f"{topics[index]} — note {number + 1}: sharing ideas, examples and discoveries."),
                        language="en", timestamp=datetime.now(timezone.utc) - timedelta(
                            hours=index * 4 + number)))
                db.session.add(Message(author=user, recipient=users[(index + 1) % len(users)],
                                       body=f"Hello from {user.username}! Welcome to the demo."))
            db.session.commit()

    # Navigation belongs to the third-party host template. Gramlot UI lives in pages/.
    template = (vendor / "app/templates/base.html").read_text()
    marker = '<ul class="navbar-nav me-auto mb-2 mb-lg-0">'
    template = template.replace(marker, marker + '\n<li class="nav-item"><a class="nav-link" '
                                'href="/gramlot/community/">Gramlot</a></li>', 1)
    app.jinja_loader = ChoiceLoader([DictLoader({"base.html": template}), app.jinja_loader])

    @app.before_request
    def optional_services():
        if request.endpoint in {"main.export_posts", "main.translate_text", "main.search",
                                "auth.reset_password_request"}:
            abort(503, "This local demo does not configure external mail, search or worker services.")

    def authorize():
        if not current_user.is_authenticated:
            if request.method == "GET" and request.path.endswith("/"):
                return redirect(url_for("auth.login", next=request.path))
            abort(401)

    handler = SqliteDbHandler(database, {"users": TableConfig("user", "id", "username")})
    try:
        mount_gramlot(app, Path(__file__).parent / "_demo", title="Microblog · Gramlot",
                      db_handler=handler, access_check=authorize)
    except Exception:
        handler.close()
        raise
    app.extensions["gramlot_demo_handler"] = handler
    return app


def close_demo(app):
    """Release caller-owned database resources when the CLI server stops."""
    app.extensions["gramlot_demo_handler"].close()
    with app.app_context():
        app.extensions["sqlalchemy"].session.remove()
        app.extensions["sqlalchemy"].engine.dispose()
