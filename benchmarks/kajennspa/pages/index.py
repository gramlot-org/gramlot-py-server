from gramlot import PageStore as SharedStore, endpoint
from gramlot_py_server.kajennspa import Page as SpaPage, PageStore as SpaStore


class PageStore(SpaStore):
    def main(self, root):
        def owner():
            return self.application.registry.page_state(
                self.page_id, connection_id=self.connection_id
            ).user

        user = owner()
        self.bind_path(
            "editor",
            self.shared_store(("bench", user), SharedStore),
            "text",
            writable=True,
            authorize=lambda: owner() == user,
        )


class Page(SpaPage):
    def main(self, root):
        panel = root.div(datapath="view")
        panel.dataBinder(".draft", "editor")
        panel.input(value="^.draft")

    @endpoint
    def echo(self, marker):
        return {"marker": marker, "user": self.state.user}
