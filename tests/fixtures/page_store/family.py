"""A primary page serving two iframe branches and connected windows."""
from gramlot import Page as BasePage


class Page(BasePage):
    title = "One WebSocket for the page family"

    def main(self, root):
        pane = root.div(class_="stack")
        pane.h1("One WebSocket for the page family")
        pane.p("Each order has its own page and server Bag. Edit either order independently.")
        pane.a("Open a connected window", href="./", target="_blank", rel="opener", id="open-child")
        pane.h2("Direct child")
        pane.iframe(src="./", id="direct-child", title="Direct order page", height="430", width="100%")
        pane.h2("Nested child")
        pane.iframe(src="branch", id="branch-child", title="Intermediate page", height="530", width="100%")
