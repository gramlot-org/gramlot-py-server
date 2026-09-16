# Microblog source

Source: https://github.com/miguelgrinberg/microblog
Revision: a975ef64864354867c88e0ed3a17ba7d17dca752
License: MIT; see LICENSE, copyright Miguel Grinberg.

The app directory and config.py are unchanged upstream source. The demo wrapper
supplies isolated configuration, fixtures and a Jinja navigation overlay. These
original Microblog pages are the third-party host application; the added Gramlot
interface is authored separately in Python. Upstream CLI translation tooling and
optional Redis, Elasticsearch, mail and translation services are outside this demo.
