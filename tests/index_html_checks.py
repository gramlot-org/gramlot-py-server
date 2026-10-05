"""Pages and paths shared by the index.html tests of every framework."""
import re

# URL below the mount path, title of the page it opens.
INDEX_HTML_PATHS = (("/", "Home"), ("/index.html", "Home"), ("/about", "About"),
                    ("/about/index.html", "About"), ("/about/", "About"))
# URLs below the mount path that answer 404.
INDEX_HTML_MISSING = ("/missing/index.html", "/about/index.htm", "/about.html")


def titled_pages(folder):
    """Write ``index.py`` (title Home) and ``about.py`` (title About) in ``folder``."""
    for name, title in (("index", "Home"), ("about", "About")):
        (folder / f"{name}.py").write_text(
            "from gramlot import Page as Base\n"
            "class Page(Base):\n"
            f"    title = {title!r}\n"
            f"    def main(self, root): root.h1({title!r})\n"
        )
    return folder


def title_of(document):
    """The text of the ``<title>`` of an HTML document."""
    return re.search(r"<title>(.*?)</title>", document).group(1)
