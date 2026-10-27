"""Uvicorn fixture: two client copies and a separate server recipe."""
from decimal import Decimal
import asyncio
from gramlot import Page as BasePage, PageStore as BasePageStore, endpoint
from genro_bag import Bag


class Page(BasePage):
    title = "PageStore WebSocket proof of concept"

    def main(self, root):
        pane = root.div(datapath="view", class_="stack")
        pane.h1("One server store, two reactive copies")
        pane.p("Edit quantity and leave the field. The server calculates the total; both copies update.")
        pane.dataBinder(".order", "order")
        pane.dataBinder(".mirror", "order")
        pane.html_label("Quantity", for_="quantity")
        pane.input(id="quantity", type="number", min="0", value="^.order.quantity")
        pane.p("Second copy")
        pane.span("^.mirror.quantity", id="mirror")
        pane.p("Total calculated on the server")
        pane.span("^.order.total", id="total")
        pane.span("^.order.status", id="status")
        pane.h2("RPC on the same connection")
        pane.input(id="rpc-input", value="^.rpc_input", placeholder="Value to send")
        pane.dataRpc("echo", result_path=".rpc_result", value="^.rpc_input")
        pane.span("^.rpc_result", id="rpc-result")
        pane.h2("Publish to the PageStore")
        pane.input(id="publish-quantity", value="^.publish_quantity", placeholder="Quantity to publish")
        pane.button("Publish quantity", id="publish-quantity-button",
                    action="gramlot.publish({topic: 'set_quantity', server: true}, {quantity});",
                    quantity="=.publish_quantity")
        pane.a("Open a connected window", href="./", target="_blank", rel="opener", id="open-child")
        pane.a("Try the iframe family", href="family")

    @endpoint
    def echo(self, value):
        return value

    @endpoint
    async def delayed_echo(self, value, delay):
        await asyncio.sleep(delay)
        return value

    @endpoint
    def failing(self):
        raise ValueError("Record not found")

    @endpoint(auth="authenticated")
    def restricted(self):
        return "Private"


class PageStore(BasePageStore):
    def main(self, root):
        self.data.set_item("order", Bag(dict(quantity="2", unit_price=Decimal("12.50"),
                                           total=Decimal("25.00"), status="Ready")))
        root.dataController(func="calculate", quantity="^order.quantity")
        root.dataController(func="set_quantity", subscribe_set_quantity=True)
        root.dataController(func="reply", subscribe_reply=True)

    def reply(self, node, value, *, _subscription_metadata):
        self.publish("received", {"record": Bag({"value": value})},
                     page_id=_subscription_metadata["pageId"])

    def set_quantity(self, node, quantity):
        self.data.set_item("order.quantity", quantity)

    def calculate(self, node, quantity):
        try:
            amount = int(quantity)
            if amount < 0:
                raise ValueError
        except (TypeError, ValueError):
            self.data.set_item("order.status", "Enter a non-negative whole quantity")
            return
        self.data.set_item("order.total", amount * self.data.get_item("order.unit_price"))
        self.data.set_item("order.status", "Calculated on the server")

