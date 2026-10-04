/** Open one Gramlot page in a real browser and check that it starts and shows a text.
 * Usage: node scripts/verify_url_browser.mjs PLAYWRIGHT_ENTRY ENGINE URL TEXT
 * The page must reach the state 'started' with no console error, no failed request and
 * no response with a status of 400 or more, and an element must have TEXT as its text.
 */
import assert from 'node:assert/strict';
import {pathToFileURL} from 'node:url';

const [playwrightEntry, engineName, url, text] = process.argv.slice(2);
if (!text) throw new Error('Usage: node scripts/verify_url_browser.mjs PLAYWRIGHT_ENTRY ENGINE URL TEXT');
const playwright = await import(pathToFileURL(playwrightEntry));
const browser = await playwright[engineName].launch({headless: true});
try {
    const page = await browser.newPage();
    const errors = [];
    page.on('pageerror', error => errors.push(String(error)));
    page.on('console', message => { if (message.type() === 'error') errors.push(message.text()); });
    page.on('requestfailed', request => errors.push(`failed ${request.url()}`));
    page.on('response', response => {
        if (response.status() >= 400) errors.push(`${response.status()} ${response.url()}`);
    });
    await page.goto(url);
    await page.waitForFunction(() => window.gramlot?.state === 'started', null, {timeout: 10000});
    await page.waitForFunction(expected => [...document.querySelectorAll('body *')]
        .some(element => element.children.length === 0 && element.textContent === expected), text, {timeout: 10000});
    assert.deepEqual(errors, [], url);
    console.log(`PASS ${engineName} ${url}: ${text}`);
} finally {
    await browser.close();
}
