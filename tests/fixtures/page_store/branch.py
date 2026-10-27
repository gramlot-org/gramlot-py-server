"""An intermediate page forwards its child through its own parent."""
from gramlot import Page as BasePage


class Page(BasePage):
    title = "Intermediate page"

    def main(self, root):
        pane = root.div(class_="stack")
        pane.h3("This page passes its child's messages to the primary")
        pane.iframe(src="./", id="nested-child", title="Nested order page", height="430", width="100%")
