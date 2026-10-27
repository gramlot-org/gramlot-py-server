/** Verify the PageStore trial through the actual gallery tree and child frames.
 * Usage: node scripts/verify_page_store_gallery.mjs URL PLAYWRIGHT_ENTRY [ENGINE ...]
 */
import assert from 'node:assert/strict';
import {pathToFileURL} from 'node:url';

const [url, entry, ...engines] = process.argv.slice(2);
if (!entry) throw new Error('Usage: verify_page_store_gallery.mjs URL PLAYWRIGHT_ENTRY [ENGINE ...]');
const playwright = await import(pathToFileURL(entry));
for (const engine of engines.length ? engines : ['chromium']) {
    const browser = await playwright[engine].launch({headless: true});
    try {
        const context = await browser.newContext({viewport: {width: 1440, height: 1000}});
        await context.addInitScript(() => {
            window.socketCount = 0;
            const Socket = window.WebSocket;
            window.WebSocket = class extends Socket {
                constructor(...args) { super(...args); window.socketCount++; }
            };
        });
        const page = await context.newPage();
        page.setDefaultTimeout(15000);
        const errors = [], httpRpc = [];
        page.on('pageerror', error => errors.push(error.message));
        page.on('console', message => { if (message.type() === 'error') errors.push(message.text()); });
        context.on('request', request => {
            if (new URL(request.url()).pathname.endsWith('/gramlot/rpc')) httpRpc.push(request.url());
        });
        await page.goto(url);
        await page.getByText('PageStore and WebSocket', {exact: true}).click();
        await page.frameLocator('iframe[src$="/90-page_store/00-index"]')
            .getByRole('heading', {name: 'PageStore and WebSocket', exact: true}).waitFor();
        await page.getByRole('button', {name: 'Expand PageStore and WebSocket', exact: true}).click();
        await page.getByRole('treeitem', {name: 'Bidirectional Bag binding', exact: true}).click();
        const order = page.frameLocator('iframe[src$="/90-page_store/01_bidirectional"]');
        await order.locator('#quantity').fill('5');
        await order.locator('#quantity').blur();
        await order.locator('#total').filter({hasText: '62.5'}).waitFor();
        assert.equal(await order.locator('#mirror-quantity').inputValue(), '5');
        await order.locator('#mirror-quantity').fill('3');
        await order.locator('#mirror-quantity').blur();
        await order.locator('#total').filter({hasText: '37.5'}).waitFor();
        assert.equal(await order.locator('#quantity').inputValue(), '3');
        await order.locator('#quantity').fill('-1');
        await order.locator('#quantity').blur();
        await order.locator('#status').filter({hasText: 'non-negative'}).waitFor();
        await order.locator('#quantity').fill('4');
        await order.locator('#quantity').blur();
        await order.locator('#total').filter({hasText: '50'}).waitFor();

        await page.getByRole('treeitem', {name: 'Publish a customer request', exact: true}).click();
        const customer = page.frameLocator('iframe[src$="/90-page_store/02_customer_lookup"]');
        async function load(key, status, name, loadedKey) {
            await customer.locator('#customer-key').fill(key);
            await customer.locator('#load-customer').click();
            await customer.locator('#customer-status').filter({hasText: status}).waitFor();
            await customer.locator('#customer-name').filter({hasText: name}).waitFor();
            assert.equal(await customer.locator('#loaded-key').textContent(), loadedKey);
        }
        await load('1', 'loaded', 'Mario Rossi', '1');
        await load('2', 'loaded', 'Anna Bianchi', '2');
        await load('99', 'error', 'Anna Bianchi', '2');
        assert.equal(await customer.locator('#customer-error').textContent(), 'Customer not found');
        await load('1', 'loaded', 'Mario Rossi', '1');
        assert.equal(await customer.locator('#customer-error').textContent(), '');
        assert.equal(await page.evaluate(() => window.socketCount), 1);
        const children = page.frames().filter(frame => /\/90-page_store\/0[12]_/.test(frame.url()));
        assert.equal(children.length, 2);
        for (const frame of children) {
            assert.equal(await frame.evaluate(() => window.socketCount), 0);
            assert.equal(await frame.evaluate(() => window.gramlot._pageStore.closed), false);
        }
        const source = await page.request.get(new URL('pages/90-page_store/02_customer_lookup.py', url).href);
        assert.equal(source.status(), 200);
        const text = await source.text();
        assert.ok(text.includes('class PageStore') && text.includes('subscribe_load_customer=True'));
        assert.ok(!text.includes('dataSetter'));
        await page.getByRole('tab', {name: 'Explanation', exact: true}).click();
        await page.getByText('Publication ok acknowledges validation and acceptance', {exact: false}).waitFor();
        await page.getByRole('tab', {name: 'Example', exact: true}).click();
        await customer.locator('#customer-name').filter({hasText: 'Mario Rossi'}).waitFor();
        assert.deepEqual(httpRpc, []);
        assert.deepEqual(errors, []);
        await page.screenshot({path: '/private/tmp/gramlot-page-store-gallery-' + engine + '.png'});
        await page.getByRole('treeitem', {name: 'Publish from a page family', exact: true}).click();
        const family = page.frameLocator('iframe[src$="/90-page_store/03_family"]');
        const direct = family.frameLocator('#direct-customer');
        const nested = family.frameLocator('#customer-branch').frameLocator('#nested-customer');
        for (const child of [direct, nested]) {
            await child.locator('#customer-status').filter({hasText: 'unset'}).waitFor();
        }
        async function loadChild(child, key, name) {
            await child.locator('#customer-key').fill(key);
            await child.locator('#load-customer').click();
            await child.locator('#customer-name').filter({hasText: name}).waitFor();
            await child.locator('#customer-status').filter({hasText: 'loaded'}).waitFor();
        }
        async function openChild(link) {
            const opened = context.waitForEvent('page');
            await link.click();
            const child = await opened;
            child.on('pageerror', error => errors.push(error.message));
            child.on('console', message => { if (message.type() === 'error') errors.push(message.text()); });
            await child.locator('#customer-status').filter({hasText: 'unset'}).waitFor();
            return child;
        }
        await loadChild(direct, '1', 'Mario Rossi');
        await loadChild(nested, '2', 'Anna Bianchi');
        const popup = await openChild(family.locator('#open-family-window'));
        const nestedPopup = await openChild(nested.locator('#open-connected-copy'));
        const leaf = await openChild(nestedPopup.locator('#open-connected-copy'));
        await loadChild(popup, '2', 'Anna Bianchi');
        await loadChild(nestedPopup, '1', 'Mario Rossi');
        await loadChild(leaf, '2', 'Anna Bianchi');
        await leaf.locator('#customer-key').fill('99');
        await leaf.locator('#load-customer').click();
        await leaf.locator('#customer-status').filter({hasText: 'error'}).waitFor();
        assert.equal(await leaf.locator('#customer-name').textContent(), 'Anna Bianchi');
        assert.equal(await direct.locator('#customer-name').textContent(), 'Mario Rossi');
        assert.equal(await nested.locator('#customer-name').textContent(), 'Anna Bianchi');
        assert.equal(await nestedPopup.locator('#customer-status').textContent(), 'loaded');
        assert.equal(await popup.locator('#customer-status').textContent(), 'loaded');
        const identities = [];
        let sockets = 0;
        for (const window of context.pages()) {
            for (const frame of window.frames()) {
                sockets += await frame.evaluate(() => window.socketCount ?? 0);
                if (frame.url().endsWith('/02_customer_lookup')) {
                    identities.push(await frame.evaluate(() => window.gramlot.pageId));
                    assert.equal(await frame.evaluate(() => window.gramlot._pageStore.closed), false);
                }
            }
        }
        assert.equal(sockets, 1);
        assert.equal(identities.length, 6); // Earlier lesson, two family frames and three popups.
        assert.equal(new Set(identities).size, identities.length);
        assert.deepEqual(errors, [], 'all family publications completed without channel errors');
        const leafClosed = leaf.waitForEvent('close');
        await nestedPopup.close();
        await leafClosed;
        assert.deepEqual(errors, [], 'intermediate popup closure');
        assert.equal(popup.isClosed(), false);
        await loadChild(direct, '2', 'Anna Bianchi');
        await loadChild(nested, '1', 'Mario Rossi');
        const framePopup = await openChild(direct.locator('#open-connected-copy'));
        await loadChild(framePopup, '1', 'Mario Rossi');
        await page.screenshot({path: '/private/tmp/gramlot-page-store-family-' + engine + '.png'});
        await page.getByRole('treeitem', {name: 'Publish to another page', exact: true}).click();
        const cross = page.frameLocator('iframe[src$="/90-page_store/05_cross_page"]');
        const recipient = cross.frameLocator('#recipient-page');
        await recipient.locator('#customer-status').filter({hasText: 'unset'}).waitFor();
        const recipientId = await recipient.locator('#current-page-id').inputValue();
        const sender = await openChild(cross.locator('#open-sender'));
        assert.notEqual(await sender.locator('#current-page-id').inputValue(), recipientId);
        await sender.locator('#cross-page-controls > summary').click();
        async function publishTo(target, key, outcome) {
            await sender.locator('#target-page-id').fill(target);
            await sender.locator('#customer-key').fill(key);
            await sender.locator('#load-on-recipient').click();
            await sender.locator('#delivery-status').filter({hasText: outcome}).waitFor();
        }
        await publishTo(recipientId, '1', 'Accepted');
        await recipient.locator('#customer-name').filter({hasText: 'Mario Rossi'}).waitFor();
        const senderId = await sender.locator('#current-page-id').inputValue();
        assert.equal(await recipient.locator('#sender-page-id').textContent(), senderId);
        await sender.locator('#event-customer-name').filter({hasText: 'Mario Rossi'}).waitFor();
        assert.equal(await sender.locator('#event-customer-key').textContent(), '1');
        assert.equal(await sender.locator('#event-store-id').textContent(), recipientId);
        assert.equal(await recipient.locator('#event-customer-name').textContent(), '');
        await publishTo(recipientId, '99', 'Accepted');
        await recipient.locator('#customer-error').filter({hasText: 'Customer not found'}).waitFor();
        assert.equal(await recipient.locator('#sender-page-id').textContent(), senderId);
        assert.equal(await sender.locator('#event-customer-name').textContent(), 'Mario Rossi');
        assert.equal(await recipient.locator('#customer-name').textContent(), 'Mario Rossi');
        await publishTo('unknown-recipient', '2', 'page_expired');
        const foreignContext = await browser.newContext();
        try {
            const foreign = await foreignContext.newPage();
            await foreign.goto(await cross.locator('#recipient-page').evaluate(element => element.src));
            await foreign.locator('#customer-status').filter({hasText: 'unset'}).waitFor();
            const foreignId = await foreign.locator('#current-page-id').inputValue();
            await publishTo(foreignId, '2', 'page_expired');
            assert.equal(await foreign.locator('#customer-status').textContent(), 'unset');
        } finally {
            await foreignContext.close();
        }
        await publishTo(recipientId, '2', 'Accepted');
        await recipient.locator('#customer-name').filter({hasText: 'Anna Bianchi'}).waitFor();
        assert.equal(await recipient.locator('#customer-status').textContent(), 'loaded');
        assert.equal(await recipient.locator('#customer-error').textContent(), '');
        assert.equal(await recipient.locator('#sender-page-id').textContent(), senderId);
        await sender.locator('#event-customer-name').filter({hasText: 'Anna Bianchi'}).waitFor();
        assert.equal(await sender.locator('#event-customer-key').textContent(), '2');
        assert.equal(await sender.locator('#event-store-id').textContent(), recipientId);
        assert.equal(await recipient.locator('#event-customer-name').textContent(), '');
        assert.equal(await sender.locator('#customer-status').textContent(), 'unset');
        assert.equal(await sender.locator('#customer-name').textContent(), '');
        sockets = 0;
        for (const window of context.pages()) {
            for (const frame of window.frames()) sockets += await frame.evaluate(() => window.socketCount ?? 0);
        }
        assert.equal(sockets, 1);
        await page.screenshot({path: '/private/tmp/gramlot-page-store-cross-page-' + engine + '.png'});
        const closed = [popup, framePopup, sender].map(child => child.waitForEvent('close'));
        await page.close();
        await Promise.all(closed);
        assert.deepEqual(httpRpc, []);
        assert.deepEqual(errors, []);
        console.log(engine + ': gallery navigation, two-way binders, customer success/error/recovery, source, explanation and one shared WebSocket passed');
        console.log(engine + ': family publications, isolated PageStores, one primary socket and recursive popup closure passed');
        console.log(engine + ': cross-page publication, validated sender metadata, reverse event to the sender subscribed controller, acceptance versus business outcome, foreign-owner refusal and recovery passed');
    } finally {
        await browser.close();
    }
}
