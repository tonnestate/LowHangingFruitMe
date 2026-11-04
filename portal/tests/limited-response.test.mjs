import test from "node:test";
import assert from "node:assert/strict";
import {readFileSync} from "node:fs";
import {readBoundedResponse,UpstreamLimitError,upstreamTimeoutMs}
 from "../lib/limited-response.mjs";

test("BFF enforces byte cap for chunked JSON without Content-Length",async()=>{
 const stream=new ReadableStream({start(ctrl){
  ctrl.enqueue(new TextEncoder().encode("abc"));
  ctrl.enqueue(new TextEncoder().encode("de"));
  ctrl.close();
 }});
 const bytes=await readBoundedResponse(new Response(stream),5);
 assert.equal(new TextDecoder().decode(bytes),"abcde");
});
test("BFF rejects declared oversize responses without allocating the body",async()=>{
 const response=new Response("small",{headers:{"Content-Length":"999999999"}});
 await assert.rejects(readBoundedResponse(response,4),UpstreamLimitError);
});
test("BFF rejects chunked oversized responses and untrusted shorter lengths",async()=>{
 for(const headers of [{},{"Content-Length":"1"}]){
  const response=new Response(new ReadableStream({start(ctrl){
   ctrl.enqueue(new TextEncoder().encode("123"));
   ctrl.enqueue(new TextEncoder().encode("456"));
   ctrl.close();
  }}),{headers});
  await assert.rejects(readBoundedResponse(response,5),UpstreamLimitError);
 }
});
test("BFF rejects malformed upstream length and invalid budgets",async()=>{
 await assert.rejects(
  readBoundedResponse(new Response("a",{headers:{"Content-Length":"broken"}}),10),
  UpstreamLimitError,
 );
 await assert.rejects(readBoundedResponse(new Response("a"),-1),TypeError);
 assert.equal((await readBoundedResponse(new Response(null,{status:204}),10)).byteLength,0);
});
test("Docling extraction has bounded end-to-end BFF and Apache time budgets",()=>{
 assert.equal(upstreamTimeoutMs("POST","/v1/contract-candidates"),135000);
 assert.equal(upstreamTimeoutMs("GET","/v1/contract-candidates"),45000);
 assert.equal(upstreamTimeoutMs("POST","/v1/audits"),45000);
 const config=readFileSync(new URL("../../deploy/apache-vhost.conf.example",import.meta.url),"utf8");
 const specific=config.indexOf("ProxyPass /api/finance/");
 const generic=config.indexOf("ProxyPass / http://127.0.0.1:3107/");
 assert.ok(specific>=0 && specific<generic);
 assert.match(config,/ProxyPass \/api\/finance\/[^\n]+timeout=150/);
});
