# Verification

Run `python scripts/check.py` for lint, pytest and paired Sphinx builds. Tests use
real Flask clients and Microblog/SQLAlchemy models. They cover context/application
isolation, page/asset delivery, traversal, typed service errors, login protection,
shared data reads, persistent seeding and CLI startup/shutdown. No external mail,
Elasticsearch or worker service is required.

`scripts/check_installed.py` verifies a wheel outside the source tree, including
plain hosting without demo/database extras, then the optional demo integration.
Browser QA covers original login, Gramlot navigation, dbSelect search, selecting
Alice, remote profile/posts and the link back to the original profile.
