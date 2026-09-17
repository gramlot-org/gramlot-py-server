from gramlot.page import WebPage, endpoint


class Page(WebPage):
    title = 'Gramlot on Genro ASGI'

    def main(self, root):
        root.data('name', 'World')
        root.data('greeting', '')
        root.h1(self.title)
        root.textbox(value='^name', label='Name')
        root.button('Greet', fire='greet')
        root.dataRpc('greeting', 'greet', name='=name', _fired='^greet')
        root.div('^greeting')

    @endpoint
    def greet(self, name: str) -> str:
        return f'Hello, {name}!'
