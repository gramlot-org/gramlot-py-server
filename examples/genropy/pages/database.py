from gramlot.page import endpoint
from gramlot_genro_asgi.genropy import GenropyPage


class Page(GenropyPage):
    """Read-only connectivity example: no application tables or credentials exposed."""

    def main(self, root):
        root.data('status', '')
        root.h1('GenroPy legacy database')
        root.button('Check connection', fire='check')
        root.dataRpc('status', 'check_connection', _fired='^check')
        root.div('^status')

    @endpoint
    def check_connection(self) -> str:
        cursor = self.db.execute('SELECT 1')
        try:
            return 'Connected' if cursor.fetchone()[0] == 1 else 'Unexpected response'
        finally:
            cursor.close()
