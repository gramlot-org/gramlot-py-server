from gramlot import Page as BasePage


class Page(BasePage):
    title = "Hello"

    def main(self, root):
        pane = root.div(datapath="person")
        pane.html_label("Name", for_="name")
        pane.input(id="name", value="^.name", live=True)
        pane.p("^.greeting")
        pane.dataFormula(".greeting", func="greeting", name="^.name", _init=True)
        pane.dataSetter(".name", "Ada")
