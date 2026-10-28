/** Real browser -> native adapter -> PageStore -> browser, sharing one socket with RPC.
 * Usage: node scripts/verify_page_store.mjs ENVIRONMENT PYTHON PLAYWRIGHT_ENTRY [ENGINE ...]
 */
import assert from 'node:assert/strict';
import {spawn} from 'node:child_process';
import {createServer} from 'node:net';
import {fileURLToPath, pathToFileURL} from 'node:url';

const [environment, python, entry, ...engines] = process.argv.slice(2);
if (!entry) throw new Error('Expected Python and Playwright entry paths');
const playwright = await import(pathToFileURL(entry));
const reserve = createServer();
await new Promise(resolve => reserve.listen(0, '127.0.0.1', resolve));
const port = reserve.address().port;
await new Promise(resolve => reserve.close(resolve));
const child = spawn(python, [fileURLToPath(new URL('serve_page_store.py', import.meta.url)), environment, String(port)],
    {stdio: ['ignore', 'pipe', 'pipe']});
let output = '';
child.stdout.on('data', chunk => { output += chunk; });
child.stderr.on('data', chunk => { output += chunk; });
try {
    await new Promise((resolve, reject) => {
        const timeout = setTimeout(() => reject(new Error(output || 'Server startup timed out')), 10000);
        const check = chunk => {
            if (String(chunk).includes('Uvicorn running')) { clearTimeout(timeout); resolve(); }
        };
        child.stderr.on('data', check);
        child.once('exit', code => { clearTimeout(timeout); reject(new Error(`Server exited ${code}: ${output}`)); });
    });
    for (const engine of engines.length ? engines : ['chromium']) {
        const browser = await playwright[engine].launch({headless: true});
        try {
            const context = await browser.newContext();
            const page = await context.newPage();
            page.context().setDefaultTimeout(15000);
            await page.context().addInitScript(() => {
                window.storeSocketCount = 0;
                const Socket = window.WebSocket;
                window.WebSocket = class extends Socket {
                    constructor(...args) { super(...args); window.storeSocketCount++; }
                };
            });
            const errors = [];
            const sockets = [];
            const httpRpcs = [];
            page.context().on('request', request => {
                if (new URL(request.url()).pathname.endsWith('/gramlot/rpc')) httpRpcs.push(request.url());
            });
            page.on('pageerror', error => errors.push(error.message));
            page.on('websocket', socket => sockets.push(socket));
            await page.goto(`http://127.0.0.1:${port}/py/`);
            await page.waitForFunction(() => window.gramlot?.data.getItem('view.order.quantity') === '2');
            await page.locator('#quantity').fill('5');
            await page.locator('#quantity').blur();
            await page.waitForFunction(() => Number(window.gramlot.data.getItem('view.order.total')) === 62.5);
            assert.equal(await page.locator('#mirror').textContent(), '5');
            assert.equal(await page.locator('#status').textContent(), 'Calculated on the server');
            assert.equal(sockets.length, 1);
            assert.equal(await page.evaluate(() => window.gramlot.rpc.call('data', 'echo', {value: 'WebSocket RPC'})),
                'WebSocket RPC');
            await page.locator('#rpc-input').fill('Declarative RPC');
            await page.locator('#rpc-input').blur();
            await page.waitForFunction(() => window.gramlot.data.getItem('view.rpc_result') === 'Declarative RPC');
            assert.equal(await page.locator('#rpc-result').textContent(), 'Declarative RPC');
            const rpcChecks = await page.evaluate(async () => {
                const rpc = window.gramlot.rpc, order = [];
                const slow = rpc.call('data', 'delayed_echo', {value: 'slow', delay: 0.1}).then(v => order.push(v));
                const fast = rpc.call('data', 'echo', {value: 'fast'}).then(v => order.push(v));
                await Promise.all([slow, fast]);
                let error;
                try { await rpc.call('data', 'failing'); } catch (e) { error = e.message; }
                const abort = new AbortController();
                const pending = rpc.call('data', 'delayed_echo', {value: 'late', delay: 0.2}, {signal: abort.signal});
                abort.abort(new Error('Cancelled by caller'));
                let cancelled;
                try { await pending; } catch (e) { cancelled = e.message; }
                return {order, error, cancelled, sync: rpc.supportsCallSync,
                    pending: window.gramlot._pageStore.calls.size};
            });
            assert.deepEqual(rpcChecks, {order: ['fast', 'slow'], error: 'Record not found',
                cancelled: 'Cancelled by caller', sync: false, pending: 0});
            assert.deepEqual(httpRpcs, []);
            // Python-authored publication activates the PageStore's subscribed controller.
            await page.locator('#publish-quantity').fill('6');
            await page.locator('#publish-quantity-button').click();
            await page.waitForFunction(() => Number(window.gramlot.data.getItem('view.order.total')) === 75);
            assert.equal(await page.locator('#mirror').textContent(), '6');
            // Client insertion and deletion must reach another binder through the server.
            await page.evaluate(() => window.gramlot.data.setItem('view.order.extra', 'temporary', {kind: 'probe'}));
            await page.waitForFunction(() => window.gramlot.data.getItem('view.mirror.extra') === 'temporary');
            await page.evaluate(() => window.gramlot.data.popNode('view.order.extra'));
            await page.waitForFunction(() => window.gramlot.data.getNode('view.mirror.extra') === null);
            assert.equal(await page.evaluate(() => window.gramlot._pageStore.error?.message ?? null), null);
            assert.deepEqual(errors, []);
            await page.evaluate(() => window.gramlot.dispose());
            console.log(`${engine}: binders, controller, declarative RPC, reverse completion, errors and cancellation on one WebSocket passed`);

            await page.goto(`http://127.0.0.1:${port}/py/family`);
            await page.waitForFunction(() => window.gramlot?._pageStore.routes.size === 3);
            const direct = await (await page.locator('#direct-child').elementHandle()).contentFrame();
            const branch = await (await page.locator('#branch-child').elementHandle()).contentFrame();
            const nested = await (await branch.locator('#nested-child').elementHandle()).contentFrame();
            async function ready(target) {
                await target.waitForFunction(() => window.gramlot?.data.getItem('view.order.quantity') === '2');
                assert.equal(await target.evaluate(() => window.storeSocketCount), 0);
                assert.equal(await target.evaluate(() => window.gramlot._pageStore.socket), null);
            }
            async function quantity(target, value) {
                await target.locator('#quantity').fill(String(value));
                await target.locator('#quantity').blur();
                await target.waitForFunction(value => Number(window.gramlot.data.getItem('view.order.total')) === value * 12.5, value);
                assert.equal(await target.locator('#mirror').textContent(), String(value));
            }
            await ready(direct); await ready(nested);
            console.log(`${engine}: direct and nested iframe snapshots received`);
            const ids = await Promise.all([page, direct, branch, nested].map(target => target.evaluate(() => window.gramlot.pageId)));
            assert.equal(new Set(ids).size, 4);
            assert.equal(await page.evaluate(() => window.storeSocketCount), 1);
            assert.equal(await branch.evaluate(() => window.storeSocketCount), 0);
            await quantity(direct, 5);
            assert.equal(await nested.locator('#quantity').inputValue(), '2');
            await quantity(nested, 7);
            assert.equal(await direct.locator('#quantity').inputValue(), '5');

            const popupPromise = page.waitForEvent('popup');
            await page.locator('#open-child').click();
            const popup = await popupPromise;
            popup.on('pageerror', error => errors.push(error.message));
            await ready(popup);
            const nestedPopupPromise = page.waitForEvent('popup');
            await nested.locator('#open-child').click();
            const nestedPopup = await nestedPopupPromise;
            nestedPopup.on('pageerror', error => errors.push(error.message));
            await ready(nestedPopup);
            console.log(`${engine}: both connected window snapshots received`);
            await quantity(popup, 9); await quantity(nestedPopup, 11);
            await page.waitForFunction(() => window.gramlot._pageStore.routes.size === 5);
            assert.equal(await nestedPopup.evaluate(() => window.gramlot.rpc.call('data', 'echo', {value: 'child WebSocket'})), 'child WebSocket');
            await nestedPopup.locator('#rpc-input').fill('Nested popup RPC');
            await nestedPopup.locator('#rpc-input').blur();
            await nestedPopup.waitForFunction(() => window.gramlot.data.getItem('view.rpc_result') === 'Nested popup RPC');
            await nestedPopup.locator('#publish-quantity').fill('12');
            await nestedPopup.locator('#publish-quantity-button').click();
            await nestedPopup.waitForFunction(() => Number(window.gramlot.data.getItem('view.order.total')) === 150);
            // Another primary, with the same owner cookie but its own socket.
            const independent = await context.newPage();
            await independent.goto(`http://127.0.0.1:${port}/py/`);
            await independent.waitForFunction(() => window.gramlot?.data.getItem('view.order.quantity') === '2');
            assert.equal(await independent.evaluate(() => window.storeSocketCount), 1);
            const independentId = await independent.evaluate(() => window.gramlot.pageId);
            assert.equal(await nestedPopup.evaluate(pageId => window.gramlot.publish(
                {topic: 'set_quantity', server: true, pageId}, {quantity: '17'}), independentId), 'ok');
            await independent.waitForFunction(() => Number(window.gramlot.data.getItem('view.order.total')) === 212.5);
            assert.equal(await nestedPopup.locator('#mirror').textContent(), '12');
            const nestedId = await nestedPopup.evaluate(() => window.gramlot.pageId);
            assert.equal(await independent.evaluate(pageId => window.gramlot.publish(
                {topic: 'set_quantity', server: true, pageId}, {quantity: '13'}), nestedId), 'ok');
            await nestedPopup.waitForFunction(() => Number(window.gramlot.data.getItem('view.order.total')) === 162.5);
            // A denied target must reject only this publication, including in a nested popup.
            const foreignContext = await browser.newContext();
            const foreign = await foreignContext.newPage();
            await foreign.goto(`http://127.0.0.1:${port}/py/`);
            await foreign.waitForFunction(() => window.gramlot?.data.getItem('view.order.quantity') === '2');
            const foreignId = await foreign.evaluate(() => window.gramlot.pageId);
            for (const sender of [independent, nestedPopup]) {
                const outcomes = await sender.evaluate(async pageId => Promise.all([
                    window.gramlot.publish({topic: 'set_quantity', server: true, pageId}, {quantity: '99'})
                        .catch(error => ({code: error.code, name: error.name})),
                    window.gramlot.rpc.call('data', 'echo', {value: 'alive'}),
                    window.gramlot.publish({topic: 'unknown', server: true}, {}),
                ]), foreignId);
                assert.deepEqual(outcomes, [{code: 'page_expired', name: 'RpcError'}, 'alive', 'ok']);
                // Valid publication, but missing the controller's required argument:
                // acceptance succeeds and the later subscriber failure cannot close the channel.
                assert.equal(await sender.evaluate(() => window.gramlot.publish(
                    {topic: 'set_quantity', server: true}, {})), 'ok');
                assert.equal(await sender.evaluate(() => window.gramlot.rpc.call(
                    'data', 'echo', {value: 'after subscriber failure'})), 'after subscriber failure');
                assert.equal(await sender.evaluate(() => window.gramlot._pageStore.closed), false);
            }
            assert.equal(await foreign.locator('#mirror').textContent(), '2');
            await foreignContext.close();
            await quantity(nestedPopup, 14);
            assert.equal(await nestedPopup.evaluate(() => window.gramlot.publish(
                {topic: 'set_quantity', server: true}, {quantity: '13'})), 'ok');
            await nestedPopup.waitForFunction(() => Number(window.gramlot.data.getItem('view.order.total')) === 162.5);
            assert.equal(await nestedPopup.evaluate(() => window.storeSocketCount), 0);
            await independent.close();
            await page.waitForFunction(() => window.gramlot._pageStore.routes.size === 5);
            console.log(`${engine}: correlated publication ok/error, rejected foreign target and continued RPC/binders passed`);
            // The same family registry also supports publications in both directions.
            assert.equal(await page.evaluate(() => window.gramlot._frames.children.length), 3);
            assert.equal(await branch.evaluate(() => window.gramlot._frames.children.length), 1);
            assert.equal(await nested.evaluate(() => window.gramlot._frames.children[0].kind), 'popup');
            await popup.evaluate(() => window.gramlot.subscribe('family_ping', data => {
                window.gramlot.publish({topic: 'family_reply', parent: true}, data);
            }));
            await page.evaluate(() => window.gramlot.subscribe('family_reply', data => window.gramlot.data.setItem('family_reply', data.value)));
            const popupId = await popup.evaluate(() => window.gramlot.pageId);
            await page.evaluate(pageId => window.gramlot.publish({topic: 'family_ping', pageId}, {value: 42}), popupId);
            await page.waitForFunction(() => window.gramlot.data.getItem('family_reply') === 42);

            // Navigation creates a new page ID; its old route must not receive the new snapshot.
            await direct.evaluate(() => location.reload());
            await direct.waitForFunction(old => window.gramlot?.pageId !== old
                && window.gramlot?.data.getItem('view.order.quantity') === '2', ids[1]);
            await page.waitForFunction(old => !window.gramlot._pageStore.routes.has(old)
                && window.gramlot._pageStore.routes.size === 5, ids[1]);
            await quantity(direct, 4);
            console.log(`${engine}: child reload completed`);

            // Removing a Source branch closes all its descendants, including its open window.
            const branchPopupClosed = nestedPopup.waitForEvent('close');
            await page.evaluate(() => {
                const node = window.gramlot.dom.getBaseSourceNode(document.getElementById('branch-child'));
                node.parentBag.popNode(node.label);
            });
            await branchPopupClosed;
            await page.waitForFunction(() => window.gramlot._pageStore.routes.size === 2);
            console.log(`${engine}: removed branch disconnected`);
            await quantity(popup, 8);
            await popup.close();
            await page.waitForFunction(() => window.gramlot._pageStore.routes.size === 1);
            await quantity(direct, 6);
            assert.equal(await page.evaluate(() => window.gramlot._pageStore.error), null);
            assert.equal(await page.evaluate(() => window.storeSocketCount), 1);
            assert.deepEqual(errors, []);
            assert.deepEqual(httpRpcs, []);
            // Closing an intermediate popup closes its own popup, preserving siblings.
            const childPromise = page.waitForEvent('popup');
            await page.locator('#open-child').click();
            const childPopup = await childPromise;
            await ready(childPopup);
            const grandPromise = childPopup.waitForEvent('popup');
            await childPopup.locator('#open-child').click();
            const grandPopup = await grandPromise;
            await ready(grandPopup);
            const grandClosed = grandPopup.waitForEvent('close');
            await childPopup.close();
            await grandClosed;
            await page.waitForFunction(() => window.gramlot._pageStore.routes.size === 1);
            await quantity(direct, 3);
            // Native primary closure cascades through popup and iframe parents.
            const lastPromise = page.waitForEvent('popup');
            await page.locator('#open-child').click();
            const lastPopup = await lastPromise;
            await ready(lastPopup);
            const leafPromise = lastPopup.waitForEvent('popup');
            await lastPopup.locator('#open-child').click();
            const leafPopup = await leafPromise;
            await ready(leafPopup);
            const framePopupPromise = page.waitForEvent('popup');
            await direct.locator('#open-child').click();
            const framePopup = await framePopupPromise;
            await ready(framePopup);
            const closed = [lastPopup, leafPopup, framePopup].map(popup => popup.waitForEvent('close'));
            await page.close();
            await Promise.all(closed);
            assert.deepEqual(errors, []);
            assert.deepEqual(httpRpcs, []);
            console.log(`${engine}: one family protocol, publish/RPC/binders, nested popup closure, Source removal and native primary closure passed`);
        } finally { await browser.close(); }
    }
} catch (error) {
    process.stderr.write(output);
    throw error;
} finally {
    child.kill('SIGTERM');
    await new Promise(resolve => { if (child.exitCode !== null) resolve(); else child.once('exit', resolve); });
}

