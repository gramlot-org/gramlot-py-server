/** Run against the chart_reports local host: PLAYWRIGHT_ENTRY URL OUTPUT_DIR. */
import {pathToFileURL} from 'node:url';
import {mkdir} from 'node:fs/promises';
import assert from 'node:assert/strict';
const [entry,url,output]=process.argv.slice(2);
const {chromium,webkit}=await import(pathToFileURL(entry));
await mkdir(output,{recursive:true});
for(const [name,engine] of Object.entries({chromium,webkit})) {
 const browser=await engine.launch();
 try {
  const page=await browser.newPage({viewport:{width:1400,height:950}}),errors=[];
  page.on('pageerror',e=>errors.push(e.message));page.setDefaultTimeout(12000);
  await page.goto(`${url}/streaming`);
  const chart=page.locator('#stream-pane-view');
  await chart.locator('.uplot canvas').waitFor();
  await page.waitForFunction(()=>window.gramlot.data.getItem('stream.sample')>5);
  const canvas=await chart.locator('canvas').elementHandle();
  const rates={};
  for(const rate of ['2','60']) {
   await page.locator('#stream-rate').selectOption(rate);
   await page.waitForTimeout(2200);
   rates[rate]=await page.evaluate(()=>window.gramlot.data.getItem('stream.measuredRate'));
   assert.ok(rates[rate]>0,`timer advances at requested ${rate} Hz`);
   assert.equal(await page.evaluate(()=>window.gramlot.data.getItem('stream.rows').getNodes().length),600);
   assert.equal(await canvas.evaluate(node=>node===document.querySelector('#stream-pane-view').shadowRoot.querySelector('canvas')),true);
  }
  await page.locator('#stream-toggle').click();
  const stopped=await page.evaluate(()=>window.gramlot.data.getItem('stream.sample'));
  await page.waitForTimeout(350);
  assert.equal(await page.evaluate(()=>window.gramlot.data.getItem('stream.sample')),stopped);
  await page.locator('#stream-pane').getByRole('button',{name:'Chart settings'}).click();
  assert.deepEqual(await page.locator('#stream-pane-chartType option').evaluateAll(nodes=>nodes.filter(n=>!n.hidden).map(n=>n.value)),['line']);
  const before=await page.evaluate(()=>window.gramlot.data.getItem('stream.config.seriesOptions').toTytx());
  for(const [engine,selector] of [['echarts','svg'],['plotly','.js-plotly-plot'],['vega','.measure0'],['uplot','.uplot canvas']]) {
   await page.locator('#stream-pane-engine').selectOption(engine);
   await chart.locator(selector).first().waitFor();
  }
  assert.equal(await page.evaluate(()=>window.gramlot.data.getItem('stream.config.seriesOptions').toTytx()),before);
  await page.setViewportSize({width:1000,height:850});
  await page.waitForTimeout(250);
  const fit=await chart.evaluate(el=>{
   const root=el.shadowRoot.querySelector('.uplot').getBoundingClientRect(),host=el.getBoundingClientRect();
   return root.width<=host.width+1&&root.height<=host.height+1;
  });assert.equal(fit,true);
  await page.screenshot({path:`${output}/${name}-drawer.png`,fullPage:true});
  await page.locator('#stream-pane').getByRole('button',{name:'Chart settings'}).click();
  await page.locator('#stream-reset').click();
  assert.equal(await page.evaluate(()=>window.gramlot.data.getItem('stream.sample')),0);
  assert.equal(await page.evaluate(()=>window.gramlot.data.getItem('stream.running')),false);
  assert.equal(await page.evaluate(()=>window.gramlot.data.getItem('stream.rows').getNodes().length),600);
  await chart.locator('canvas').waitFor();
  await page.locator('#stream-rate').selectOption('30');await page.locator('#stream-toggle').click();
  await page.waitForFunction(()=>window.gramlot.data.getItem('stream.sample')>15);
  await page.screenshot({path:`${output}/${name}-streaming.png`,fullPage:true});
  assert.deepEqual(errors,[]);
  console.log(`${name}: 600-sample window, pause/reset/resume, four engines, resize and settings passed; observed timer Hz ${JSON.stringify(rates)}`);
  await page.close();
 } finally {await browser.close();}
}
