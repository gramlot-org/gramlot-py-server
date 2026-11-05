/** Real-data qualification: 20 cursor changes per engine; two animation frames included. */
import {pathToFileURL} from 'node:url';
const [entry,url,output]=process.argv.slice(2);
if(!output)throw new Error('Usage: PLAYWRIGHT_ENTRY HOST_URL OUTPUT_DIR');
const {chromium,webkit}=await import(pathToFileURL(entry));
import assert from 'node:assert/strict';
import {mkdir,writeFile} from 'node:fs/promises';
await mkdir(output,{recursive:true});const results=[];
for(const [browserName,engine] of Object.entries({chromium,webkit})){
 const browser=await engine.launch();
 try{
  const page=await browser.newPage({viewport:{width:1450,height:1100}}),errors=[];
  page.setDefaultTimeout(30000);page.on('pageerror',e=>{errors.push(e.message);console.log(e.stack);});
  let started=performance.now();await page.goto(`${url.replace(/\/$/,'')}/australian_timeline`);
  await page.waitForFunction(()=>window.gramlot?.data.getItem('sales.count')>0);
  const pane=page.locator('#sales-pane'),view=page.locator('#sales-pane-view');await view.locator('svg').waitFor();
  const loadMs=performance.now()-started;
  assert.equal(await page.locator('#sales-error').innerText(),'');
  await pane.scrollIntoViewIfNeeded();
  await pane.getByRole('button',{name:'Chart settings'}).click();
  await pane.getByRole('menuitem',{name:'Choose measures',exact:true}).click();
  await page.getByRole('menuitemcheckbox',{name:'Units',exact:true}).click();
  assert.equal(await page.evaluate(()=>window.gramlot.data.getItem('salesChart.valueFields')),'revenue,invoices,units');
  await page.locator('#sales-pane-chartType').selectOption('line');await page.locator('#sales-pane-captionField').selectOption('rank');
  for(const grain of ['month','day']){
   let reloadMs=null;
   if(grain==='day'){
    started=performance.now();await page.locator('#sales-grain').selectOption('day');
    await page.waitForFunction(()=>window.gramlot.data.getItem('sales.grain')==='day'&&!window.gramlot.data.getItem('loading'));
    reloadMs=performance.now()-started;
   }
   const meta=await page.evaluate(()=>Object.fromEntries(['count','source_lines','source_invoices','query_ms','prepare_ms','total'].map(k=>[k,window.gramlot.data.getItem('sales.'+k)])));
   assert.equal(meta.source_lines,410429);assert.equal(meta.source_invoices,60179);assert.equal(meta.count,grain==='month'?384:11612);
   for(const [renderer,marker] of [['echarts','svg'],['plotly','.js-plotly-plot'],['vega','.measure0'],['uplot','.uplot canvas']]){
    await page.locator('#sales-pane-engine').selectOption(renderer);await view.locator(marker).first().waitFor();await page.waitForTimeout(250);
    const timings=await page.evaluate(async()=>{
     const data=window.gramlot.data,times=[],dispatch=[];
     for(let i=1;i<=20;i++){
      const start=performance.now();data.setItem('salesChart.timeIndex',i);dispatch.push(performance.now()-start);
      await new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)));
      times.push(performance.now()-start);
     }
     return {times,dispatch};
    });
    assert.equal(await view.getByRole('alert').isVisible(),false);
    const search=page.getByRole('searchbox',{name:'Filter rows'});
    await search.evaluate(input=>{
     window.filterTiming=new Promise(resolve=>input.addEventListener('input',()=>{
      const start=performance.now();
      const check=()=>{
       const v=window.gramlot.src.binding.nodeIds.get('salesGrid').gridSearch.view,rows=v.getRows();
       if(rows.length&&rows.every(row=>v.value(row,'territory')==='Tasmania'))requestAnimationFrame(()=>requestAnimationFrame(()=>resolve(performance.now()-start)));
       else requestAnimationFrame(check);
      };requestAnimationFrame(check);
     },{once:true}));
    });
    await search.fill('Tasmania');const filterMs=await page.evaluate(()=>window.filterTiming);
    assert.equal(await view.getByRole('alert').isVisible(),false);
    if(renderer==='plotly'){
     const traces=await view.locator('.js-plotly-plot').evaluate(el=>el.data);
     assert.equal(traces.length,3);assert.ok(traces.every(t=>t.y.length===1));
    }
    await search.fill('');await page.waitForTimeout(250);
    const samples=timings.times.sort((a,b)=>a-b),dispatch=timings.dispatch.sort((a,b)=>a-b);
    results.push({browser:browserName,grain,engine:renderer,...meta,initial_load_ms:Math.round(loadMs),reload_ms:reloadMs&&Math.round(reloadMs),dispatch_median_ms:+dispatch[10].toFixed(2),dispatch_p95_ms:+dispatch[18].toFixed(2),update_median_ms:+samples[10].toFixed(1),update_p95_ms:+samples[18].toFixed(1),filter_observed_ms:Math.round(filterMs)});
    console.log(JSON.stringify(results.at(-1)));
   }
  }
  await page.locator('#sales-pane-engine').selectOption('echarts');await page.locator('#sales-pane-chartType').selectOption('bar');await page.locator('#sales-pane-captionField').selectOption('code');
  await pane.getByRole('button',{name:'Chart settings'}).click();await page.waitForTimeout(1200);await page.screenshot({path:`${output}/${browserName}.png`,fullPage:true});
  assert.deepEqual(errors,[]);await page.close();
 }finally{await browser.close();await writeFile(`${output}/metrics.json`,JSON.stringify(results,null,2));}
}
