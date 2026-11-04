import test from "node:test";
import assert from "node:assert/strict";
import {verifiedApiPath,trustedApiOrigin,sameOrigin} from "../lib/private-api.mjs";

test("BFF exposes only financial service allowlist",()=>{
 const id="12345678-1234-4abc-9def-123456789012";
 assert.equal(verifiedApiPath("GET",["me"]),"/v1/me");
 assert.equal(verifiedApiPath("POST",["audits",id,"billing-packets"]),"/v1/audits/"+id+"/billing-packets");
 assert.equal(verifiedApiPath("GET",["billing-packets",id]),"/v1/billing-packets/"+id);
 assert.equal(verifiedApiPath("POST",["billing-packets",id,"release"]),"/v1/billing-packets/"+id+"/release");
 assert.equal(verifiedApiPath("POST",["billing-packets",id,"void"]),"/v1/billing-packets/"+id+"/void");
 assert.equal(verifiedApiPath("DELETE",["billing-packets",id]),null);
 assert.equal(verifiedApiPath("POST",["contract-candidates"]),"/v1/contract-candidates");
 assert.equal(verifiedApiPath("POST",["contract-candidates",id,"review"]),"/v1/contract-candidates/"+id+"/review");
 assert.equal(verifiedApiPath("GET",["contract-candidates",id]),"/v1/contract-candidates/"+id);
 assert.equal(verifiedApiPath("PUT",["uploads",id,"content"]),"/v1/uploads/"+id+"/content");
 assert.equal(verifiedApiPath("POST",["audits",id,"recovery-events"]),
              "/v1/audits/"+id+"/recovery-events");
 assert.equal(verifiedApiPath("GET",["audits",id,"fee-ledger"]),
              "/v1/audits/"+id+"/fee-ledger");
 assert.equal(verifiedApiPath("POST",["audits",id,"case-status"]),
              "/v1/audits/"+id+"/case-status");
 for(const fmt of ["pdf","xlsx","json"]){
   assert.equal(verifiedApiPath("GET",["audits",id,"report."+fmt]),
                "/v1/audits/"+id+"/report."+fmt);
 }
 assert.equal(verifiedApiPath("GET",["audits",id,"report.exe"]),null);
 for(const path of [["../../etc/passwd"],["openapi.json"],["approval"],["uploads","other","content"]]){
   assert.equal(verifiedApiPath("GET",path),null);
 }
 assert.equal(verifiedApiPath("DELETE",["uploads",id]),null);
});
test("internal financial API is loopback only, never an arbitrary SSRF target",()=>{
 assert.equal(trustedApiOrigin("http://127.0.0.1:8107"),"http://127.0.0.1:8107");
 for(const input of ["https://evil.example","http://localhost:8107",
                     "http://127.0.0.1:81","http://127.0.0.1:8107/admin",
                     "http://user:password@127.0.0.1:8107",undefined]){
   assert.equal(trustedApiOrigin(input),null);
 }
});
test("cross-origin modifications are forbidden",()=>{
 assert.equal(sameOrigin("https://portal.example/app","https://portal.example"),true);
 assert.equal(sameOrigin("https://portal.example/app","https://attacker.example"),false);
 assert.equal(sameOrigin("https://portal.example/app",null),false);
});
