/** Real JSONL on the floating Grid and timing lesson; never logs record contents. */
import assert from 'node:assert/strict';
const {loadSelectionTrial}=await import(process.argv[2]);
const base=process.argv[3];
async function open(path) {
    const response=await fetch(base+path);
    assert.equal(response.status,200);
    const cookie=response.headers.getSetCookie().map(value=>value.split(';')[0]).join('; ');
    const html=await response.text(), pageId=/"pageId":"([^"]+)"/.exec(html)[1];
    return {pageId,fetcher:(url,options)=>fetch(base+url,{...options,headers:{...options.headers,Cookie:cookie}})};
}
const floating=await open('/pages/82-grid-database/02-invoice_rows');
const lesson=await open('/pages/83-selection-trials/02-jsonl');
for(const limit of ['1000','100000']) {
    const options={url:'/gramlot/selection-trial',method:'load_trial_rows',limit,signal:new AbortController().signal};
    const left=await loadSelectionTrial({...options,...floating});
    const right=await loadSelectionTrial({...options,...lesson});
    const a=left.selection.getItem('rows').getNodes(),b=right.selection.getItem('rows').getNodes();
    assert.equal(a.length,Number(limit));assert.equal(a.length,b.length);
    for(let i=0;i<a.length;i++)assert.deepEqual(a[i].attr,b[i].attr);
    console.log(JSON.stringify({rows:a.length,allFieldsEqual:true,floating:left.metrics,lesson:right.metrics}));
}
const controller=new AbortController();
await assert.rejects(loadSelectionTrial({url:'/gramlot/selection-trial',pageId:lesson.pageId,method:'load_trial_rows',limit:'100000',signal:controller.signal,
    fetcher:async(url,options)=>{const response=await lesson.fetcher(url,options);controller.abort();return response;}}),{name:'AbortError'});
const forbidden=await fetch(`${base}/gramlot/selection-trial`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id:'unowned',pageId:lesson.pageId,contentType:'data',name:'load_trial_rows',params:{limit:'100'}})});
assert.equal(forbidden.status,400);
for(const page of ['/pages/83-selection-trials/01-json','/pages/83-selection-trials/03-websocket-rpc'])assert.equal((await fetch(base+page)).status,404);
console.log('Cancellation, unowned-page refusal and retired routes passed');
