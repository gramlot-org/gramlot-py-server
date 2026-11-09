"""Terminal fixture: sessions of a PageStore reached through /gramlot/terminal."""
from gramlot import Page as BasePage, PageStore as BasePageStore, endpoint
from gramlot.page import terminal


class Page(BasePage):
    title = "Terminal sessions"

    def main(self, root):
        root.div("Terminal")

    @endpoint
    def echo(self, value):
        return value


class PageStore(BasePageStore):
    @terminal
    async def echo(self, session):
        while data := await session.read():
            await session.write(data)

    @terminal
    async def sizes(self, session):
        while (size := await session.resized()) is not None:
            await session.write(f"{size[0]}x{size[1]}".encode())

    @terminal
    async def flood(self, session):
        for _ in range(48):
            await session.write(b"x" * 65536)

    @terminal
    async def bye(self, session):
        await session.write(b"bye")

    @terminal
    async def peer(self, session):
        await session.write(f"{session.host} {session.client}".encode())

    @terminal
    async def held(self, session):
        while True:
            await session.write(b"x" * 65536)

    @terminal(auth="admin")
    async def guarded(self, session):
        await session.write(b"secret")
