import test from 'node:test';
import assert from 'node:assert/strict';
import worker from '../newsletter/collector/worker.mjs';
const request = (body, origin='https://fedregintel.com') => new Request('https://collector.example/signup', {method:'POST',headers:{Origin:origin,'Content-Type':'application/json'},body:JSON.stringify(body)});
test('collector validates consent and challenge before storing; errors do not claim success', async () => {
  const originalFetch = globalThis.fetch;
  const writes=[];
  const env={TURNSTILE_SECRET:'test',DB:{prepare:sql=>({bind:(...args)=>({run:async()=>{writes.push({sql,args});}})})}};
  try {
    globalThis.fetch = async()=>Response.json({success:true,hostname:'fedregintel.com',action:'signup'});
    assert.equal((await worker.fetch(request({email:'a@example.com',consent:true,token:'test'},'https://evil.example'),env)).status,403);
    assert.equal((await worker.fetch(request({email:'a@example.com',consent:false,token:'test'}),env)).status,400);
    assert.equal((await worker.fetch(request({email:'invalid',consent:true,token:'test'}),env)).status,400);
    assert.equal((await worker.fetch(request({email:'a@example.com',consent:true}),env)).status,400);
    assert.equal(writes.length,0);
    const result=await worker.fetch(request({email:' A@example.com ',consent:true,token:'test'}),env);
    assert.equal(result.status,200);
    assert.equal(writes[0].args[0],'a@example.com');
    assert.equal(writes[0].args[4],'pending-launch-unverified');
    assert.match(writes[0].sql,/ON CONFLICT\(email\) DO NOTHING/);
    globalThis.fetch=async()=>Response.json({success:false});
    assert.equal((await worker.fetch(request({email:'b@example.com',consent:true,token:'bad'}),env)).status,400);
    assert.equal(writes.length,1);
    globalThis.fetch=async()=>Response.json({success:true,hostname:'evil.example',action:'signup'});
    assert.equal((await worker.fetch(request({email:'b@example.com',consent:true,token:'bad'}),env)).status,400);
    assert.equal(writes.length,1);
    globalThis.fetch=async()=>Response.json({success:true,hostname:'fedregintel.com',action:'signup'});
    env.DB.prepare=()=>{throw new Error('storage down');};
    assert.equal((await worker.fetch(request({email:'b@example.com',consent:true,token:'test'}),env)).status,503);
  } finally {globalThis.fetch=originalFetch;}
});
