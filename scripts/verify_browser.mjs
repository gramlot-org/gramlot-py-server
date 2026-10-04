/** Real-browser check of the five adapters under the mount path /py.
 * Usage: node scripts/verify_browser.mjs PYTHON PLAYWRIGHT_ENTRY [ENGINE …]
 * PYTHON has gramlot-py-server installed with every framework extra. For each adapter,
 * scripts/serve_adapter.py serves a pages folder at /py with the strict CSP profile and
 * an assets map. Checks: /py answers 301 to /py/, whose page shows an image of the
 * assets map by a relative URL; foo.py takes its Logic from the page module foo.js.
 */
import assert from 'node:assert/strict';
import {spawn} from 'node:child_process';
import {mkdtemp, mkdir, rm, writeFile} from 'node:fs/promises';
import {createServer} from 'node:net';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {fileURLToPath, pathToFileURL} from 'node:url';

const [python, playwrightEntry, ...engines] = process.argv.slice(2);
if (!playwrightEntry) throw new Error('Usage: node scripts/verify_browser.mjs PYTHON PLAYWRIGHT_ENTRY [ENGINE …]');
const playwright = await import(pathToFileURL(playwrightEntry));
const SERVE = fileURLToPath(new URL('serve_adapter.py', import.meta.url));
const FRAMEWORKS = ['uvicorn', 'django', 'flask', 'fastapi', 'kajenn'];

const indexPage = `from gramlot import Page as Base


class Page(Base):
    title = "Index"

    def main(self, root):
        root.h1("Index", id="title")
        root.img(src="assets/branding/logo.svg", alt="Logo", id="logo")
`;
const fooPage = `from gramlot import Page as Base


class Page(Base):
    title = "Page module"

    def main(self, root):
        root.div("^out", id="out")
        root.dataFormula("out", func="greet", name="^name", _init=True)
        root.dataSetter("name", "Ada")
`;
const fooModule = `import {Page as BasePage} from '@gramlot/gramlot/page';

export class Page extends BasePage {
    main(root) { root.h1('The JavaScript version, unused by the Python host'); }
}

export class Logic {
    greet(kwargs) { return \`Hello, \${kwargs.name}\`; }
}
`;
const logo = '<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10"><rect width="10" height="10"/></svg>';

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

async function startAdapter(framework, pages, assets) {
    const port = await freePort();
    const child = spawn(python, [SERVE, framework, pages, String(port), JSON.stringify(assets)],
        {stdio: ['ignore', 'ignore', 'pipe']});
    let log = '';
    child.stderr.on('data', chunk => { log += chunk; });
    const url = `http://127.0.0.1:${port}`;
    for (let attempt = 0; attempt < 100; attempt += 1) {
        if (child.exitCode !== null) throw new Error(`${framework} exited: ${child.exitCode}\n${log}`);
        try {
            if ((await fetch(`${url}/py/`)).ok) return {url, close: () => child.kill()};
        } catch { /* not listening yet */ }
        await new Promise(resolve => setTimeout(resolve, 100));
    }
    child.kill();
    throw new Error(`${framework} did not start\n${log}`);
}

async function open(browser, url, label) {
    const page = await browser.newPage();
    const errors = [], requests = [];
    page.on('pageerror', error => errors.push(String(error)));
    page.on('console', message => { if (message.type() === 'error') errors.push(message.text()); });
    page.on('requestfailed', request => errors.push(`failed ${request.url()}`));
    page.on('response', response => {
        if (response.status() >= 400) errors.push(`${response.status()} ${response.url()}`);
    });
    page.on('request', request => requests.push(new URL(request.url()).pathname));
    const response = await page.goto(url);
    await page.waitForFunction(() => window.gramlot?.state === 'started', null, {timeout: 10000});
    return {page, errors, requests, response, label};
}

const folder = await mkdtemp(join(tmpdir(), 'gramlot-py-server-browser-'));
let browser;
const adapters = [];
try {
    const pages = join(folder, 'pages');
    await mkdir(pages);
    await writeFile(join(pages, 'index.py'), indexPage);
    await writeFile(join(pages, 'foo.py'), fooPage);
    await writeFile(join(pages, 'foo.js'), fooModule);
    await writeFile(join(folder, 'logo.svg'), logo);
    const assets = {'/assets/branding/logo.svg': {file: join(folder, 'logo.svg'), type: 'image/svg+xml'}};
    for (const framework of FRAMEWORKS) adapters.push([framework, await startAdapter(framework, pages, assets)]);

    for (const engineName of engines.length ? engines : ['chromium']) {
        browser = await playwright[engineName].launch({headless: true});
        for (const [framework, {url}] of adapters) {
            const index = await open(browser, `${url}/py`, `${engineName} ${framework} /py`);
            assert.equal(new URL(index.page.url()).pathname, '/py/', `${index.label}: redirected`);
            assert.equal((await index.response.request().redirectedFrom()?.response())?.status(), 301,
                `${index.label}: 301`);
            assert.equal(await index.page.locator('#title').textContent(), 'Index', index.label);
            assert.ok(await index.page.locator('#logo').evaluate(image => image.complete && image.naturalWidth > 0),
                `${index.label}: logo of the assets map`);
            assert.deepEqual(index.errors, [], index.label);
            await index.page.close();
            console.log(`PASS ${index.label}`);

            const foo = await open(browser, `${url}/py/foo`, `${engineName} ${framework} /py/foo`);
            assert.equal(await foo.page.locator('#out').textContent(), 'Hello, Ada', foo.label);
            assert.equal(foo.requests.filter(item => item === '/py/assets/gramlot.js').length, 1,
                `${foo.label}: one runtime`);
            assert.ok(foo.requests.includes('/py/foo.js'), `${foo.label}: foo.js imported`);
            assert.deepEqual(foo.errors, [], foo.label);
            await foo.page.close();
            console.log(`PASS ${foo.label}`);
        }
        await browser.close();
        browser = null;
    }
} finally {
    await browser?.close();
    for (const [, adapter] of adapters) adapter.close();
    await rm(folder, {recursive: true, force: true});
}
