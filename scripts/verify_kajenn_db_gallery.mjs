/** Real gallery -> Kajenn -> Asqueel/SQLite, including descendant windows.
 * Usage: node scripts/verify_kajenn_db_gallery.mjs PYTHON PLAYWRIGHT_ENTRY [ENGINE ...]
 */
import assert from 'node:assert/strict';
import {spawn} from 'node:child_process';
import {createServer} from 'node:net';
import {mkdtemp, rm} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {fileURLToPath, pathToFileURL} from 'node:url';

const [python, entry, ...engines] = process.argv.slice(2);
const playwright = await import(pathToFileURL(entry));
for (const engine of engines.length ? engines : ['chromium']) {
    const folder = await mkdtemp(join(tmpdir(), 'gramlot-db-browser-'));
    const reserve = createServer();
    await new Promise(resolve => reserve.listen(0, '127.0.0.1', resolve));
    const port = reserve.address().port;
    await new Promise(resolve => reserve.close(resolve));
    const server = spawn(python, [fileURLToPath(new URL('serve_kajenn_db_gallery.py', import.meta.url)),
        '--database', join(folder, 'customers.sqlite'), '--port', String(port)], {stdio: ['ignore','pipe','pipe']});
    let output = '';
    server.stdout.on('data', chunk => { output += chunk; });
    server.stderr.on('data', chunk => { output += chunk; });
    let browser;
    try {
        await new Promise((resolve, reject) => {
            const timer = setTimeout(() => reject(new Error(`Server startup timed out: ${output}`)), 20000);
            server.stderr.on('data', chunk => {
                if (String(chunk).includes('Uvicorn running')) { clearTimeout(timer); resolve(); }
            });
            server.once('exit', code => { clearTimeout(timer); reject(new Error(`Server exited ${code}: ${output}`)); });
        });
        browser = await playwright[engine].launch({headless:true});
        const context = await browser.newContext({viewport:{width:1440,height:1000}});
        context.setDefaultTimeout(15000);
        const sockets = [], errors = [];
        context.on('page', page => {
            page.on('websocket', socket => sockets.push(socket.url()));
            page.on('pageerror', error => errors.push(error.message));
        });
        const page = await context.newPage();
        await page.goto(`http://127.0.0.1:${port}/py/`);
        await page.getByText('Kajenn and Asqueel', {exact:true}).click();
        await page.frameLocator('iframe[src$="/91-kajenn_db/00-index"]').getByRole('heading', {name:'Kajenn and Asqueel',exact:true}).waitFor();
        await page.getByRole('button', {name:'Expand Kajenn and Asqueel',exact:true}).click();
        await page.getByRole('treeitem', {name:'Load and save a customer',exact:true}).click();
        const single = page.frameLocator('iframe[src$="/91-kajenn_db/01_customer"]');
        async function status(view, state) {
            await view.locator('#customer-status').filter({hasText:new RegExp(`^${state}$`)}).waitFor();
        }
        async function customerName(view, name) {
            const deadline = Date.now() + 15000;
            while (await view.locator('#customer-name').inputValue() !== name && Date.now() < deadline) {
                await new Promise(resolve => setTimeout(resolve, 50));
            }
            assert.equal(await view.locator('#customer-name').inputValue(), name);
        }
        async function load(view, key, name) {
            await view.locator('#customer-status').filter({hasText:/^(unset|loaded|saved|error)$/}).waitFor();
            await view.locator('#customer-key').fill(key);
            await view.locator('#customer-key').blur();
            await view.locator('#loaded-key').filter({hasText:new RegExp(`^${key}$`)}).waitFor();
            await status(view,'loaded');
            await customerName(view,name);
        }
        async function save(view, name) {
            await view.locator('#customer-name').fill(name);
            await view.locator('#save-customer').click();
            await status(view,'saved');
            assert.equal(await view.locator('#customer-error').textContent(),'');
        }
        async function reload(view, name) {
            await view.locator('#reload-customer').click();
            await status(view,'loaded');
            await customerName(view,name);
        }
        await load(single,'1','Mario Rossi');
        await save(single,'Mario saved in gallery');
        await reload(single,'Mario saved in gallery');
        await single.locator('#customer-name').fill('');
        await single.locator('#save-customer').click();
        await status(single,'error');
        assert.match(await single.locator('#customer-error').textContent(),/Name is required/);
        await reload(single,'Mario saved in gallery');
        await single.locator('#customer-email').fill('anna@example.com');
        await single.locator('#save-customer').click();
        await status(single,'error');
        assert.notEqual(await single.locator('#customer-error').textContent(),'');
        await reload(single,'Mario saved in gallery');
        assert.equal(await single.locator('#customer-email').inputValue(),'mario@example.com');
        await single.locator('#customer-key').fill('99');
        await single.locator('#customer-key').blur();
        await status(single,'error');
        assert.equal(await single.locator('#loaded-key').textContent(),'1');
        assert.equal(await single.locator('#customer-name').inputValue(),'Mario saved in gallery');
        console.log(`${engine}: real reads, commit, missing key, validation and database rollback passed`);

        await page.getByRole('treeitem',{name:'Customer editing across windows',exact:true}).click();
        const family = page.frameLocator('iframe[src$="/91-kajenn_db/02_family"]');
        const direct = family.frameLocator('#direct-customer');
        const nested = family.frameLocator('#customer-branch').frameLocator('#nested-customer');
        await load(direct,'1','Mario saved in gallery');
        await load(nested,'2','Anna Bianchi');
        const popupPromise = page.waitForEvent('popup');
        await family.locator('#open-family-window').click();
        const popup = await popupPromise;
        await load(popup,'1','Mario saved in gallery');
        await save(popup,'Mario saved in window');
        assert.equal(await direct.locator('#customer-name').inputValue(),'Mario saved in gallery');
        await reload(direct,'Mario saved in window');
        await save(nested,'Anna saved in nested frame');
        await load(popup,'2','Anna saved in nested frame');
        await save(direct,'Mario saved in direct frame');
        await load(popup,'1','Mario saved in direct frame');
        const grandchildPromise = popup.waitForEvent('popup');
        await popup.locator('#open-customer-window').click();
        const grandchild = await grandchildPromise;
        await load(grandchild,'1','Mario saved in direct frame');
        await save(grandchild,'Mario saved in grandchild');
        await reload(direct,'Mario saved in grandchild');
        assert.equal(sockets.length,1,`Expected one primary socket: ${sockets}`);
        const closed = grandchild.waitForEvent('close');
        await popup.close();
        await closed;
        assert.deepEqual(errors,[]);
        console.log(`${engine}: direct/nested frames and descendant windows read/save with one primary socket`);
    } catch (error) {
        console.error(error);
        console.error(output);
        throw error;
    } finally {
        if (browser) await browser.close();
        if (server.exitCode === null) {
            const stopped = new Promise(resolve => server.once('exit',resolve));
            server.kill('SIGTERM');
            const forced = setTimeout(() => server.kill('SIGKILL'), 5000);
            await stopped;
            clearTimeout(forced);
        }
        await rm(folder,{recursive:true,force:true});
    }
}
