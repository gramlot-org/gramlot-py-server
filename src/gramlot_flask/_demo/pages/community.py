"""Python-authored Gramlot exploration of Microblog's existing models."""
from flask import url_for
from flask_login import current_user
from gramlot.database import DbPageMixin
from gramlot.page import WebPage, source


class Page(DbPageMixin, WebPage):
    title = "Microblog community"

    def main(self, root):
        root.data("selected_user", current_user.id)
        root.css(".community", "max-width:1000px;margin:0 auto;padding:28px;font-family:system-ui")
        root.css(".post-card", "padding:16px;margin:12px 0;border:1px solid #dbe2ea;border-radius:8px")
        pane = root.div(class_="community")
        pane.a("← Back to Microblog", href=url_for("main.index"))
        pane.h1("Microblog community")
        pane.p("Explore people and their posts using Gramlot.")
        pane.dbSelect(dbtable="users", value="^selected_user", lbl="Find a member",
                      width="100%", placeholder="Search by username")
        detail = pane.contentPane()
        detail.remote(self.member, user_id="^selected_user", _delay=1)

    @source
    def member(self, root, user_id=None):
        from app import db
        from app.models import User, Post
        import sqlalchemy as sa

        if user_id is None:
            root.p("Choose a member to see their profile and posts.")
            return
        if isinstance(user_id, str) and user_id.isascii() and user_id.isdecimal():
            user_id = int(user_id)
        if isinstance(user_id, bool) or not isinstance(user_id, int):
            root.p("Unknown member.")
            return
        user = db.session.get(User, user_id)
        if user is None:
            root.p("Unknown member.")
            return
        root.h2(user.username)
        root.p(user.about_me or "No profile description yet.")
        root.p(f"{user.posts_count()} posts · {user.followers_count()} followers · "
               f"{user.following_count()} following")
        root.a("Open original profile", href=url_for("main.user", username=user.username))
        root.h3("Latest posts")
        posts = db.session.scalars(sa.select(Post).where(Post.user_id == user.id)
                                   .order_by(Post.timestamp.desc()).limit(20)).all()
        for post in posts:
            card = root.article(class_="post-card")
            card.p(post.body)
            card.small(post.timestamp.strftime("%Y-%m-%d %H:%M"))
        if not posts:
            root.p("No posts yet.")
