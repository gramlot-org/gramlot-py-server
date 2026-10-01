from gramlot import Page as BasePage


class Page(BasePage):
    title = "Greeting"

    def main(self, root):
        pane = root.div(datapath="person", class_="greeting")
        pane.html_label("Name", for_="name")
        pane.input(id="name", value="^.name", live=True)
        pane.p("^.greeting", id="greeting")
        pane.dataFormula(".greeting", func="greet", name="^.name", _init=True)
        pane.dataSetter(".name", "Ada")
