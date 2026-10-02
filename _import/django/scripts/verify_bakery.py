# Copyright 2026 Softwell S.r.l. - SPDX-License-Identifier: Apache-2.0
"""Check the running, seeded Bakery demo with a real browser (optional Playwright)."""
import argparse


def main():
    from playwright.sync_api import expect, sync_playwright
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url', default='http://127.0.0.1:8065')
    args = parser.parse_args()
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        errors, requests = [], []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.on('response', lambda response: errors.append(f'{response.status}: {response.url}')
                if response.status >= 400 else None)
        page.on('request', lambda request: requests.append(request.url))
        page.goto(args.url.rstrip('/') + '/products/explore/')
        expect(page.locator('#product-title')).to_have_text('Anadama', timeout=20000)
        products = page.locator('.explorer-list').get_by_role('row')
        expect(products).to_have_count(12)
        assert page.locator('.explorer-list gnr-grid').evaluate(
            "grid => grid.collectionStore().storeNode.getAttr('storeCode')") == 'products'
        products.nth(2).click()
        expect(page.locator('#product-title')).to_have_text('Anpan')
        categories = page.locator('.explorer-types').get_by_role('row')
        expect(categories.filter(has_text='Yeast bread').get_by_role('gridcell').last).to_have_text('3')
        expect(categories.filter(has_text='Flatbread').first.get_by_role('gridcell').last).to_have_text('2')
        categories.filter(has_text='Cornbread').click()
        expect(products).to_have_count(2)
        expect(page.locator('#product-title')).to_have_text('Arepa')
        categories.filter(has_text='Sweet bun').click()
        expect(products).to_have_count(2)
        expect(page.locator('#product-title')).to_have_text('Anpan')
        categories.filter(has_text='All breads').click()
        expect(products).to_have_count(12)
        expect(page.locator('#product-title')).to_have_text('Anadama')
        # Empty grid areas must reveal the host background in either theme.
        for theme in ('light', 'dark'):
            page.emulate_media(color_scheme=theme)
            page.reload()
            expect(page.locator('#product-title')).to_have_text('Anadama')
            expect(page.locator('html')).to_have_attribute('data-theme', theme)
            for grid in page.locator('.product-explorer gnr-grid').all():
                backgrounds = grid.evaluate("""grid => ['.frame', '.horizontal-scroll'].map(
                    selector => getComputedStyle(grid.shadowRoot.querySelector(selector)).backgroundColor)""")
                assert backgrounds == ['rgba(0, 0, 0, 0)'] * 2, (theme, backgrounds)
                grid.evaluate("grid => grid.style.setProperty('--grid-bg', 'rgb(12, 34, 56)')")
                assert grid.evaluate("grid => getComputedStyle(grid.shadowRoot.querySelector('.frame')).backgroundColor") == 'rgb(12, 34, 56)'
                grid.evaluate("grid => grid.style.removeProperty('--grid-bg')")
            page.get_by_role('button', name='Open inspector', exact=True).click()
            inspector = page.locator('gramlot-inspector')
            inspector.locator('[data-inspector="data"]').get_by_text('category', exact=True).first.click()
            cell = inspector.locator('[data-inspector="data-editor"] .inspector-property-value:visible').first
            expect(cell).to_be_visible()
            expected_background = 'rgb(21, 33, 54)' if theme == 'dark' else 'rgb(255, 255, 255)'
            expect(cell).to_have_css('background-color', expected_background)
            expect(cell.locator('input')).to_have_css('color',
                'rgb(220, 231, 248)' if theme == 'dark' else 'rgb(38, 52, 75)')
        page.locator('#toggle-page-source').click()
        source = page.locator('#page-source-panel .cm-content')
        expect(source).to_have_attribute('contenteditable', 'false')
        text = page.locator('#page-source-panel gnr-codemirror').evaluate('(editor) => editor.value')
        assert 'panel.rpcStore' in text and 'panel.dataRpc' in text and 'dataController' not in text
        assert any('/rpc/data/load_categories' in url for url in requests)
        assert sum('/rpc/data/load_products' in url for url in requests) >= 4
        assert sum('/rpc/data/load_product' in url for url in requests) >= 4
        assert not errors, errors
        browser.close()
        print('Bakery: RPC filtering, category counts, selection, transparent grids, inspector themes and readonly source passed.')


if __name__ == '__main__':
    main()
