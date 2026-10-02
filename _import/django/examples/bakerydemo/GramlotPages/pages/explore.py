"""A public catalogue with reactive Python services for lists and details."""
from pathlib import Path

from django.db.models import Count
from django.http import Http404
from django.shortcuts import get_object_or_404
from genro_bag import Bag
from gramlot.grid import GridStruct
from gramlot.page import endpoint
from gramlot_django import DjangoPage
from wagtail.models import Site

from bakerydemo.breads.models import BreadPage


class Page(DjangoPage):
    def main(self, root):
        root.h1('Explore our breads', class_='explorer-title')
        root.p('A world of bread, one selection at a time.', class_='explorer-intro')
        layout = root.div(class_='product-explorer')
        # Layout: categories, product list, then image and details.
        categories = layout.div(role='region', class_='explorer-types', aria_label='Find your bread')
        products = layout.div(role='region', class_='explorer-list', aria_label='Our breads')
        detail = layout.div(role='region', class_='explorer-detail', aria_label='Selected bread')
        self.category_grid(categories)
        self.product_grid(products)
        self.product_image(detail)
        self.product_detail(detail)
        self.source_viewer(root)

    def category_grid(self, panel):
        panel.data('category', 'all')
        panel.rpcStore(self.load_categories, storeCode='categories', storepath='categories',
                       _identifier='id', _on_start=True)
        panel.h2('Find your bread')
        panel.p('Choose a style, then explore our breads.', class_='explorer-hint')
        # The struct declares the columns; the store supplies the records.
        struct = GridStruct()
        rows = struct.view().rows()
        rows.cell('name', name='Style', width=155)
        rows.cell('count', name='Breads', dtype='L', width=60)
        panel.data('category_struct', struct)
        panel.grid(store='categories', structpath='category_struct',
                   selectedKey='^category', height='270px', aria_label='Find your bread')

    def product_grid(self, panel):
        # After loading a category, select its first product (or clear the detail).
        panel.rpcStore(self.load_products, storeCode='products', storepath='products',
                       _identifier='id', category='^category', _on_start=True,
                       _onResult='this.SET("selected", result.rows[0]?.id ?? null);')
        panel.h2('Our breads')
        panel.p('Select a row · use ↑ ↓ to browse', class_='explorer-hint')
        struct = GridStruct()
        rows = struct.view().rows()
        rows.cell('title', name='Bread', width=170)
        rows.cell('origin__title', name='Origin', width=135)
        panel.data('product_struct', struct)
        panel.grid(store='products', structpath='product_struct',
                   selectedKey='^selected', height='405px', aria_label='Our breads')

    def product_image(self, panel):
        panel.img(src='^detail.image', alt='^detail.title', hidden='^detail.no_image', class_='explorer-photo')

    def product_detail(self, panel):
        panel.data('detail', self.load_product())
        # Coalesce the grid's selection reset and the new selected row.
        panel.dataRpc('detail', self.load_product, selected='^selected', _delay=50)
        panel.p('^detail.category', class_='explorer-eyebrow')
        panel.h2('^detail.title', id='product-title', aria_live='polite')
        panel.p('^detail.description', class_='explorer-description')
        panel.h3('Ingredients')
        panel.p('^detail.ingredients', id='product-ingredients')
        panel.a('Discover this bread →', href='^detail.url', hidden='^detail.no_link', class_='explorer-link')

    def source_viewer(self, root):
        # Show this actual file; the editor never writes back to the server.
        root.data('source_hidden', True)
        root.data('page_source', Path(__file__).read_text(encoding='utf-8'))
        root.button('〈/〉  Python source', id='toggle-page-source', aria_controls='page-source-panel',
                    action='this.SET("source_hidden", !this.GET("source_hidden"));')
        panel = root.contentPane(hidden='^source_hidden', id='page-source-panel', style='margin-top:20px;')
        panel.h2('How this page works')
        panel.codeMirror(value='^page_source', language='python', readonly=True,
                         lbl='Explore Python source', style='--code-editor-height:520px;')

    def breads(self):
        # Every service is restricted to this site's published products.
        site = Site.find_for_request(self.request)
        if site is None:
            raise Http404('No bakery site')
        return BreadPage.objects.descendant_of(site.root_page).live().public()

    @endpoint
    def load_categories(self):
        # Group published breads by type and include an unfiltered entry.
        breads = self.breads()
        groups = (breads.order_by('bread_type__title')
                  .values('bread_type_id', 'bread_type__title')
                  .annotate(count=Count('pk')))
        rows = [{'id': 'all', 'name': 'All breads', 'count': breads.count()}]
        rows.extend({'id': group['bread_type_id'] or 0,
                     'name': group['bread_type__title'] or 'Other breads',
                     'count': group['count']} for group in groups)
        return self.selection_result(rows)

    @endpoint
    def load_products(self, category='all'):
        breads = self.breads()
        if category != 'all':
            breads = breads.filter(bread_type_id=category or None)
        return self.selection_result(breads.order_by('title'),
                                     fields=['id', 'title', 'origin__title'])

    @endpoint
    def load_product(self, selected=None):
        if not selected:
            return Bag({'title': 'Select a bread', 'description': '', 'image': '', 'no_image': True,
                        'ingredients': '—', 'category': '', 'origin': '', 'url': '', 'no_link': True})
        bread = get_object_or_404(
            self.breads().select_related('image', 'origin', 'bread_type').prefetch_related('ingredients'),
            pk=selected)
        category = str(bread.bread_type) if bread.bread_type else 'Other breads'
        image = ''
        if bread.image:
            try:
                image = bread.image.get_rendition('fill-900x650').url
            except FileNotFoundError:
                pass  # A missing demo image must not hide the product.
        url = bread.get_url(request=self.request) or ''
        return Bag({'title': bread.title, 'origin': str(bread.origin) if bread.origin else '—',
                    'category': category, 'description': bread.introduction,
                    'image': image, 'no_image': not image,
                    'ingredients': ', '.join(item.name for item in bread.ingredients.all()) or 'Not specified',
                    'url': url, 'no_link': not url})
