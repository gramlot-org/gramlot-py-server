/** Verify the local report host in Chromium/WebKit with ECharts and a selected comparison engine.
 * Usage: node scripts/verify_chart_reports.mjs PLAYWRIGHT_ENTRY URL OUTPUT_DIR [plotly|vega]
 */
import {pathToFileURL} from 'node:url';
import {mkdir} from 'node:fs/promises';
import assert from 'node:assert/strict';
const [playwrightEntry,url,output,comparisonEngine='plotly']=process.argv.slice(2);
if(!['plotly','vega'].includes(comparisonEngine))throw new Error('Comparison engine must be plotly or vega');
const comparisonMark=comparisonEngine==='plotly'?'.js-plotly-plot .main-svg':'.measure0';
if(!output)throw new Error('Usage: PLAYWRIGHT_ENTRY URL OUTPUT_DIR [plotly|vega]');
const {chromium,webkit}=await import(pathToFileURL(playwrightEntry));
await mkdir(output,{recursive:true});
for(const [engineName,engine] of Object.entries({chromium,webkit})){
 const browser=await engine.launch();
 try{
 for(const route of ['attributes','values','index']){
  const page=await browser.newPage({viewport:{width:1400,height:1050}}),errors=[];
  page.setDefaultTimeout(15000);page.on('pageerror',e=>errors.push(e.message));
  await page.goto(`${url.replace(/\/$/,'')}/${route}`);
  const waitPeriod=async year=>page.waitForFunction(year=>document.querySelector('#loaded-period')?.textContent.includes(`${year} vs`),year);
  await waitPeriod('2025');
  await page.locator('#bars-pane-view svg').waitFor();await page.locator('#map-pane-view svg').waitFor();
  assert.match(await page.locator('#loaded-count').textContent(),route==='index'?/8/:/2/);
  const original=await page.locator('#bars-pane-view').elementHandle();
  await page.locator('#map-pane').getByRole('button',{name:'Chart settings'}).click();
  const mapMeasure=page.locator('#map-pane-mapValueField');
  assert.equal(await mapMeasure.inputValue(),'per_customer');
  await mapMeasure.selectOption('change_pct');
  await page.locator('#map-pane').getByRole('button',{name:'Chart settings'}).click();
  await page.locator('#bars-pane').getByRole('button',{name:'Chart settings'}).click();
  await page.locator('#bars-pane-engine').selectOption(comparisonEngine);
  await page.locator(`#bars-pane-view ${comparisonMark}`).first().waitFor();
  await page.locator('#bars-pane-chartType').selectOption('line');
  await page.locator('#bars-pane').getByRole('button',{name:'Chart settings'}).click();
  const search=page.getByRole('searchbox',{name:'Filter rows'});
  await search.fill(route==='index'?'Tasmania':'Alpha');
  await page.waitForTimeout(300);
  const year=page.locator('#report-year'),reload=page.locator('#reload-report');
  await year.selectOption('2024');await reload.click();await waitPeriod('2024');
  assert.equal(await original.evaluate(el=>el===document.querySelector('#bars-pane-view')),true);
  assert.equal(await search.inputValue(),route==='index'?'Tasmania':'Alpha');
  await page.waitForFunction(({engine,code})=>{
   const root=document.querySelector('#bars-pane-view').shadowRoot;
   return engine==='plotly'?root.querySelector('.js-plotly-plot')?.data?.[0]?.y?.length===1:
     root.querySelector('.role-axis-label')?.textContent===code;
  },{engine:comparisonEngine,code:route==='index'?'TAS':'A'});
  assert.match(await page.locator('#map-pane-view svg').textContent(),/Annual change/);
  await search.fill('');
  await year.selectOption('2030');await reload.click();await waitPeriod('2030');
  await page.waitForFunction(()=>document.querySelector('#bars-pane-view').shadowRoot.textContent.includes('No data to display'));
  await year.selectOption('2025');await reload.click();await waitPeriod('2025');
  await page.locator('#map-pane-view svg').waitFor();
  await page.locator('#map-pane').getByRole('button',{name:'Chart settings'}).click();
  assert.equal(await mapMeasure.inputValue(),'change_pct');
  await page.locator('#map-pane').getByRole('button',{name:'Chart settings'}).click();
  await year.selectOption('2022');await reload.click();
  await page.waitForFunction(()=>document.querySelector('#report-error').textContent.length>0);
  assert.match(await page.locator('#loaded-period').textContent(),/2025 vs 2024/);
  assert.ok(await page.locator('#map-pane-view svg').isVisible());
  await year.selectOption('2023');await reload.click();await waitPeriod('2023');
  assert.equal(await page.locator('#report-error').textContent(),'');
  await page.locator('#bars-pane').getByRole('button',{name:'Chart settings'}).click();
  assert.equal(await page.locator('#bars-pane-chartType').inputValue(),'line');
  assert.equal(await page.locator('#bars-pane-engine').inputValue(),comparisonEngine);
  await page.locator(`#bars-pane-view ${comparisonEngine==='vega'?'svg':comparisonMark}`).first().waitFor();
  if(comparisonEngine==='vega')assert.ok(await page.locator('#bars-pane-view .measure0 path').getAttribute('d'));
  if(route!=='index'){
   assert.equal(await page.locator('#bars-pane-captionField option[value=units]').count(),1);
   assert.equal(await page.locator('#bars-pane-captionField option[value=per_customer]').count(),0);
  }
  await page.locator('#bars-pane').getByRole('button',{name:'Chart settings'}).click();
  assert.deepEqual(errors,[]);
  await page.screenshot({path:`${output}/${engineName}-${route}.png`,fullPage:true});
  await page.close();console.log(`${engineName}/${route}: ECharts map and ${comparisonEngine} line: reload, shared filter, empty recovery, failure retention and configuration passed`);
 }
 }finally{await browser.close();}
}
