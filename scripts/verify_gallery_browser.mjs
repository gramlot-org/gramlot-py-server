/** Real-browser check of `gramlot <environment> gallery` for the five environments.
 * Usage: node scripts/verify_gallery_browser.mjs PYTHON PLAYWRIGHT_ENTRY [ENGINE …]
 * PYTHON has gramlot-py-server installed with every framework extra and the extra gallery.
 * For each environment the gallery is started with --mount /py and without a prefix.
 * Under /py: /py answers 301 to /py/; the gallery page shows its logo and opens e01 in its
 * frame; every example it links starts without errors or failed requests; c03 calls its
 * Logic through the <key>_aux.js stub; <environment>-01 shows "Hello, Ada". Without a
 * prefix: the gallery, c03 and <environment>-01 at the site root.
 */
import assert from 'node:assert/strict';
import {spawn} from 'node:child_process';
import {createServer} from 'node:net';
import {pathToFileURL} from 'node:url';

const [python, playwrightEntry, ...engines] = process.argv.slice(2);
if (!playwrightEntry) throw new Error('Usage: node scripts/verify_gallery_browser.mjs PYTHON PLAYWRIGHT_ENTRY [ENGINE …]');
const playwright = await import(pathToFileURL(playwrightEntry));
const ENVIRONMENTS = ['uvicorn', 'django', 'flask', 'fastapi', 'kajenn'];

function freePort() {
    return new Promise((resolve, reject) => {
        const server = createServer();
        server.once('error', reject);
        server.listen(0, '127.0.0.1', () => {
            const {port} = server.address();
            server.close(() => resolve(port));
        });
    });
}

async function startGallery(environment, mount) {
    const port = await freePort();
    const args = ['-m', 'gramlot_py_server.cli', environment, 'gallery', '--port', String(port)];
    if (mount) args.push('--mount', mount);
    const child = spawn(python, args, {stdio: ['ignore', 'pipe', 'pipe']});
    let log = '';
    child.stdout.on('data', chunk => { log += chunk; });
    child.stderr.on('data', chunk => { log += chunk; });
    const url = `http://127.0.0.1:${port}${mount}`;
    for (let attempt = 0; attempt < 150; attempt += 1) {
        if (child.exitCode !== null) throw new Error(`${environment} gallery exited: ${child.exitCode}\n${log}`);
        try {
            if ((await fetch(`${url}/`)).ok) return {url, close: () => child.kill()};
        } catch { /* not listening yet */ }
        await new Promise(resolve => setTimeout(resolve, 100));
    }
    child.kill();
    throw new Error(`${environment} gallery did not start\n${log}`);
}

async function open(browser, url, label) {
    const page = await browser.newPage();
    const errors = [];
    page.on('pageerror', error => errors.push(String(error)));
    page.on('console', message => { if (message.type() === 'error') errors.push(message.text()); });
    page.on('requestfailed', request => errors.push(`failed ${request.url()}`));
    page.on('response', response => {
        if (response.status() >= 400) errors.push(`${response.status()} ${response.url()}`);
    });
    const response = await page.goto(url);
    await page.waitForFunction(() => window.gramlot?.state === 'started', null, {timeout: 10000});
    return {page, errors, response, label};
}

async function checkPage(browser, url, label, check) {
    const opened = await open(browser, url, label);
    if (check) await check(opened.page);
    assert.deepEqual(opened.errors, [], label);
    await opened.page.close();
}

const c03 = async page => {
    await page.fill('#price', '120');
    await page.waitForFunction(() => document.getElementById('final').textContent === '108');
};
const quickStart = async page => {
    await page.waitForFunction(() => [...document.querySelectorAll('p')].some(p => p.textContent === 'Hello, Ada'));
};

let browser;
try {
    for (const engineName of engines.length ? engines : ['chromium']) {
        browser = await playwright[engineName].launch({headless: true});
        for (const environment of ENVIRONMENTS) {
            for (const mount of ['/py', '']) {
                const gallery = await startGallery(environment, mount);
                const label = `${engineName} ${environment} ${mount || '/'}`;
                try {
                    const index = await open(browser, mount ? gallery.url : `${gallery.url}/`, `${label} index`);
                    if (mount) {
                        assert.equal(new URL(index.page.url()).pathname, `${mount}/`, `${label}: redirected`);
                        assert.equal((await index.response.request().redirectedFrom()?.response())?.status(), 301,
                            `${label}: 301`);
                    }
                    assert.ok(await index.page.locator('.gallery-logo').evaluate(image => image.complete && image.naturalWidth > 0),
                        `${label}: logo`);
                    const keys = await index.page.$$eval('a[id^="open-"]', links => links
                        .map(link => link.getAttribute('href')).filter(href => !href.startsWith('#')));
                    assert.ok(keys.includes('e01') && keys.includes(`${environment}-01`), `${label}: links`);
                    await index.page.click('#open-e01');
                    const frame = index.page.frameLocator('#frame-e01');
                    await frame.locator('body').waitFor();
                    await index.page.waitForFunction(() =>
                        document.getElementById('frame-e01').contentWindow.gramlot?.state === 'started');
                    assert.deepEqual(index.errors, [], `${label} index`);
                    await index.page.close();
                    const routes = mount ? keys : ['c03', `${environment}-01`];
                    for (const key of routes) {
                        const check = key === 'c03' ? c03 : key === `${environment}-01` ? quickStart : null;
                        await checkPage(browser, `${gallery.url}/${key}`, `${label} ${key}`, check);
                    }
                    console.log(`PASS ${label}: gallery, ${routes.length} examples, Logic of c03, ${environment}-01`);
                } finally {
                    gallery.close();
                }
            }
        }
        await browser.close();
        browser = null;
    }
} finally {
    await browser?.close();
}
