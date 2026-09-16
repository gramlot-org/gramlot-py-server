"""A Python-authored single-page community explorer for Microblog."""
from flask import current_app, url_for
from flask_login import current_user
from genro_bag import Bag
from gramlot.database import DbPageMixin
from gramlot.page import WebPage, source


class Page(DbPageMixin, WebPage):
    title = "Microblog community · Gramlot SPA"
    source_inspection = {"launcher": False}

    def main(self, root):
        root.data("selected_user", current_user.id)
        root.data("source_display", "none")
        root.styleSheet("""
            body { margin:0; background:#f1f5f9; }
            .community { max-width:1240px; margin:0 auto; padding:32px;
                font:14px/1.6 system-ui,sans-serif; color:#23344b;
                --accent-color:#127f85; --field-focus-border:#127f85;
                --form-field-radius:7px; --field-border:#d6dfe8; }
            .community * { box-sizing:border-box; }
            .community a { color:#11777e; text-decoration:none; }
            .community a:hover { text-decoration:underline; }
            .community-top { display:flex; align-items:center; justify-content:space-between;
                gap:16px; margin-bottom:26px; flex-wrap:wrap; }
            .community-actions { display:flex; gap:10px; align-items:center; }
            .community button { cursor:pointer; font:600 13px system-ui; border:1px solid #cfdae4;
                border-radius:8px; padding:10px 15px; background:white; color:#23344b; }
            .community button:hover { background:#e9f3f4; border-color:#127f85; }
            .community button:focus-visible { outline:3px solid #72cdd1; outline-offset:3px; }
            .community .inspector-icon { font-size:18px; padding:6px 12px; }
            .community-hero { background:#132b43; color:white; border-radius:16px;
                padding:30px 34px; display:flex; gap:28px; justify-content:space-between;
                align-items:center; margin-bottom:24px; }
            .community-kicker { color:#89d8d4; font-size:11px; font-weight:700;
                letter-spacing:2px; text-transform:uppercase; }
            .community h1 { margin:8px 0; font-size:34px; letter-spacing:-1px; line-height:1.2; }
            .community-hero p { margin:0; color:#c1d0df; max-width:58ch; }
            .community-search { padding:20px 24px; background:white; border:1px solid #dee5ed;
                border-radius:12px; margin-bottom:24px; }
            .community-search p { margin:0 0 12px; color:#65768a; font-size:13px; }
            .community-layout { display:grid; grid-template-columns:260px minmax(0,1fr); gap:24px; }
            .community-panel { background:white; border:1px solid #dee5ed; border-radius:12px;
                padding:24px; min-width:0; }
            .community-profile { align-self:start; }
            .community-avatar { width:58px; height:58px; display:flex; align-items:center;
                justify-content:center; background:#e4f3f1; color:#14757a; border-radius:16px;
                font-size:25px; font-weight:700; }
            .community h2 { margin:16px 0 6px; font-size:23px; letter-spacing:-.5px; }
            .community h3 { margin:0; font-size:18px; }
            .community-bio { color:#65768a; font-size:13px; }
            .community-stats { display:grid; grid-template-columns:repeat(3,1fr); gap:8px;
                padding:18px 0; margin:18px 0; border-top:1px solid #edf1f5;
                border-bottom:1px solid #edf1f5; }
            .community-stat strong { display:block; font-size:20px; color:#132b43; }
            .community-stat span { font-size:10px; color:#65768a; }
            .community-section-head { display:flex; align-items:baseline; gap:14px;
                justify-content:space-between; margin-bottom:16px; }
            .community-muted { color:#65768a; font-size:12px; }
            .community-preview { padding:18px 20px; background:#f4f8fb; border-radius:9px;
                margin-top:20px; border-left:3px solid #159299; }
            .community-preview p { margin:8px 0 0; white-space:pre-wrap; overflow-wrap:anywhere; }
            .community-source { background:#fff; border:1px solid #ccdbe5;
                border-radius:12px; padding:20px; margin-bottom:24px; }
            .community-source gnr-codemirror { --code-editor-height:440px;
                --code-editor-font-size:12px; }
            .community-footnote { color:#7b899a; font-size:12px; margin-top:20px; }
            @media(max-width:800px) { .community { padding:18px; }
                .community-layout { grid-template-columns:1fr; }
                .community-hero { padding:24px; } .community h1 { font-size:28px; }
                .community-panel { padding:18px; } }
        """)
        pane = root.div(class_="community")
        top = pane.div(class_="community-top")
        top.a("← Microblog", href=url_for("main.index"))
        actions = top.div(class_="community-actions")
        actions.button("View Python source", action=(
            "this.SET('source_display', this.GET('source_display') === 'none' ? 'block' : 'none');"))
        actions.button("🔍", class_="inspector-icon", title="Open Gramlot inspector",
                       action="gramlot.inspector.toggle();", **{"aria-label": "Open inspector"})
        hero = pane.header(class_="community-hero").div()
        hero.div("SPA EXAMPLE · GRAMLOT", class_="community-kicker")
        hero.h1("Microblog community")
        hero.p("One community, a new perspective. Explore members and their posts in a "
               "single-page application built with Gramlot.")

        code = pane.div(class_="community-source", display="^source_display")
        code_head = code.div(class_="community-section-head")
        code_head.h3("Python source")
        code_head.button("Close source", action="this.SET('source_display', 'none');")
        code.p("The Python page behind this example.", class_="community-muted")
        source_text = current_app.extensions["gramlot"]["/gramlot"].page_sources["community"]
        code.codeMirror(value=source_text, language="python", readonly=True,
                        **{"aria-label": "Example Python source"})

        search = pane.div(class_="community-search")
        search.p("Choose a member to explore their activity. The page updates without navigation.")
        search.dbSelect(dbtable="users", value="^selected_user", lbl="Find a member",
                        width="100%", placeholder="Search by username")
        pane.contentPane().remote(self.member, user_id="^selected_user", _delay=1)
        pane.p("Microblog data and login · Gramlot interface", class_="community-footnote")

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
        layout = root.div(class_="community-layout")
        profile = layout.aside(class_="community-panel community-profile")
        profile.div(user.username[:2].upper(), class_="community-avatar")
        profile.h2(user.username)
        profile.p(user.about_me or "No profile description yet.", class_="community-bio")
        stats = profile.div(class_="community-stats")
        for label, count in [("Posts", user.posts_count()), ("Followers", user.followers_count()),
                             ("Following", user.following_count())]:
            item = stats.div(class_="community-stat")
            item.strong(str(count))
            item.span(label)
        profile.a("Open original profile ↗", href=url_for("main.user", username=user.username))
        posts = db.session.scalars(sa.select(Post).where(Post.user_id == user.id)
                                   .order_by(Post.timestamp.desc()).limit(20)).all()
        rows = Bag()
        for post in posts:
            rows.set_item(f"p{post.id}", Bag({"published": post.timestamp.strftime("%Y-%m-%d %H:%M"),
                                             "body": post.body, "language": post.language or "—"}))
        root.data("posts", rows)
        root.data("selected_post", f"p{posts[0].id}" if posts else None)
        root.data("post_preview", posts[0].body if posts else "No posts yet.")
        root.dataController("this.SET('post_preview', key ? this.GET('posts.' + key + '.body') : 'Choose a post.');",
                            key="^selected_post")
        panel = layout.div(class_="community-panel")
        heading = panel.div(class_="community-section-head")
        heading.h3("Latest posts")
        heading.span(f"{len(posts)} shown · latest 20", class_="community-muted")
        grid = panel.quickGrid(value="^posts", selectedKey="^selected_post", height="300px",
                               width="100%", **{"aria-label": "Member posts"})
        grid.column("published", name="Published", width=155)
        grid.column("body", name="Post", width=460)
        grid.column("language", name="Language", width=90)
        preview = panel.div(class_="community-preview")
        preview.span("SELECTED POST", class_="community-muted")
        preview.p("^post_preview")
