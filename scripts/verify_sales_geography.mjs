import {pathToFileURL} from 'node:url';
import {mkdir} from 'node:fs/promises';
const [entry,url,output]=process.argv.slice(2);
if(!output)throw new Error('Usage: PLAYWRIGHT_ENTRY HOST_URL OUTPUT_DIR');
const {chromium,webkit}=await import(pathToFileURL(entry));
await mkdir(output,{recursive:true});
import assert from 'node:assert/strict';
for(const [name,engine] of Object.entries({chromium,webkit})){
 const browser=await engine.launch();
 try{
  const page=await browser.newPage({viewport:{width:1450,height:1150}}),errors=[];
  page.setDefaultTimeout(30000);page.on('pageerror',e=>{errors.push(e.message);console.log(e.stack);});
  await page.goto(`${url.replace(/\/$/,'')}/australian_geography`);
  await page.waitForFunction(()=>window.gramlot?.data.getItem('sales.count')===8);
  const view=page.locator('#geography-pane-view');await view.locator('svg').waitFor();
  assert.equal(await page.locator('#geo-error').innerText(),'');
  console.log(name,'national map ready');
  await view.getByText('Tasmania',{exact:true}).click();
  await page.waitForFunction(()=>window.gramlot.data.getItem('sales.state')==='TAS'&&!window.gramlot.data.getItem('loading'));
  assert.equal(await view.getByRole('alert').isVisible(),false);
  assert.equal(await page.locator('#geo-title').innerText(),'Tasmania');
  console.log(name,'drilldown',await page.evaluate(()=>({rows:window.gramlot.data.getItem('sales.count'),boundaries:window.gramlot.data.getItem('sales.boundaries'),unmatched:window.gramlot.data.getItem('sales.unmatched')})));
  await page.waitForTimeout(800);await page.screenshot({path:`${output}/tasmania-${name}.png`,fullPage:true});
  await page.locator('#geography-pane').getByRole('button',{name:'Chart settings'}).click();
  await page.locator('#geography-pane-mapValueField').selectOption('customers');
  await page.locator('#geo-year').selectOption('2024');
  await page.waitForFunction(()=>window.gramlot.data.getItem('sales.year')==='2024'&&!window.gramlot.data.getItem('loading'));
  await page.getByRole('searchbox',{name:'Filter rows'}).fill('Yes');
  await page.waitForTimeout(350);
  await page.locator('#geo-home').click();
  await page.waitForFunction(()=>window.gramlot.data.getItem('sales.state')===''&&!window.gramlot.data.getItem('loading'));
  assert.equal(await page.getByRole('searchbox',{name:'Filter rows'}).inputValue(),'Yes');
  assert.equal(await page.locator('#geo-year').inputValue(),'2024');
  assert.equal(await page.locator('#geography-pane-mapValueField').inputValue(),'customers');
  await page.locator('#geography-pane-engine').selectOption('plotly');
  await view.locator('.js-plotly-plot').waitFor();await page.waitForTimeout(1000);
  // A real pointer click on the SVG geographic path exercises Plotly's event adapter.
  const states=await view.locator('.choroplethlayer path').count();console.log(name,'plotly paths',states);
  await view.locator('.choroplethlayer path').filter({visible:true}).first().click({force:true});
  await page.waitForFunction(()=>window.gramlot.data.getItem('sales.state')!==''&&!window.gramlot.data.getItem('loading'));
  assert.equal(await view.getByRole('alert').isVisible(),false);
  await page.locator('#geography-pane').getByRole('button',{name:'Chart settings'}).click();
  await page.waitForTimeout(800);await page.screenshot({path:`${output}/${name}.png`,fullPage:true});
  assert.deepEqual(errors,[]);console.log(name,'two-engine navigation, year/measure/filter retention passed');
 }finally{await browser.close();}
}
