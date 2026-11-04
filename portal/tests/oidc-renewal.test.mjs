import test from "node:test";
import assert from "node:assert/strict";
import {checkedTokenEndpoint,authCookieName,sessionCookieNames,
 clearAuthCookies,rotateAuthCookies,renewApiCredential} from "../lib/oidc-renewal.mjs";

test("refresh endpoint is pinned to HTTPS issuer and its path",()=>{
 assert.equal(checkedTokenEndpoint(
  "https://identity.example/realms/client",
  "https://identity.example/realms/client/protocol/openid-connect/token"),
  "https://identity.example/realms/client/protocol/openid-connect/token");
 for(const endpoint of [
  "http://identity.example/realms/client/token",
  "https://attacker.example/realms/client/token",
  "https://identity.example/realms/other/token",
  "https://identity.example@attacker.example/token",
  "https://identity.example/realms/client/token?redirect=evil",
 ]){
  assert.throws(()=>checkedTokenEndpoint(
   "https://identity.example/realms/client",endpoint),/OIDC_CONFIG_INVALID/);
 }
});

test("refresh only sends credentials to pinned origin and rotates token",async()=>{
 let called=0;
 const r=await renewApiCredential({
  issuer:"https://identity.example/realms/client",
  tokenEndpoint:"https://identity.example/realms/client/protocol/openid-connect/token",
  clientId:"client-app",clientSecret:"only-for-unit-tests",
  refreshToken:"test-refresh-unique-001",
  now:()=>1700000000000,
  fetcher:async(url,init)=>{
   called++;
   assert.equal(new URL(url).host,"identity.example");
   assert.equal(init.redirect,"error");
   assert.equal(init.method,"POST");
   assert.equal(init.body.get("refresh_token"),"test-refresh-unique-001");
   assert.equal(init.body.get("grant_type"),"refresh_token");
   return new Response(JSON.stringify({
    access_token:"synthetic-new-access",expires_in:600,
    refresh_token:"synthetic-rotated-refresh",token_type:"Bearer",
   }),{status:200});
  },
 });
 assert.equal(called,1);
 assert.deepEqual(r,{accessToken:"synthetic-new-access",
  expiresAt:1700000600,refreshToken:"synthetic-rotated-refresh"});
});

test("renewal is singleflight for concurrent requests",async()=>{
 let requests=0;
 const config={
  issuer:"https://issuer.example/tenant",
  tokenEndpoint:"https://issuer.example/tenant/token",
  clientId:"app",clientSecret:"test-only",refreshToken:"singleflight-002",
  fetcher:async()=>{
   requests++;
   await new Promise(resolve=>setTimeout(resolve,30));
   return new Response(JSON.stringify({access_token:"new",
    expires_in:300}),{status:200});
  },
 };
 const [a,b]=await Promise.all([renewApiCredential(config),renewApiCredential(config)]);
 assert.equal(requests,1);
 assert.deepEqual(a,b);
 assert.equal(a.refreshToken,config.refreshToken);
});

test("revoked or oversized token responses fail closed",async()=>{
 const base={
  issuer:"https://issuer.example/tenant",
  tokenEndpoint:"https://issuer.example/tenant/token",
  clientId:"app",clientSecret:"test-only",
 };
 await assert.rejects(renewApiCredential({
  ...base,refreshToken:"revoked-003",
  fetcher:async()=>new Response('{"error":"invalid_grant"}',{status:400}),
 }),/OIDC_REFRESH_REJECTED/);
 await assert.rejects(renewApiCredential({
  ...base,refreshToken:"unbounded-004",
  fetcher:async()=>new Response("a".repeat(20000),{status:200}),
 }),/OIDC_REFRESH_REJECTED/);
 await assert.rejects(renewApiCredential({
  ...base,refreshToken:"malformed-005",
  fetcher:async()=>new Response(JSON.stringify({
   access_token:"x",expires_in:"3600",
  }),{status:200}),
 }),/OIDC_REFRESH_REJECTED/);
});

test("auth cookie rotation handles chunks without exposing bearer value",()=>{
 assert.equal(authCookieName(true),"__Secure-authjs.session-token");
 const old=[{name:"__Secure-authjs.session-token",value:"old"},
  {name:"__Secure-authjs.session-token.4",value:"old-part"},
  {name:"not-session",value:"keep"}];
 assert.equal(sessionCookieNames(old,true).length,2);
 const value="a".repeat(4200);
 const updated=rotateAuthCookies(value,old,true);
 assert.ok(updated.some(x=>x.startsWith("__Secure-authjs.session-token.0=")));
 assert.ok(updated.some(x=>x.startsWith("__Secure-authjs.session-token.1=")));
 assert.ok(updated.some(x=>x.startsWith("__Secure-authjs.session-token=;")));
 assert.ok(updated.every(x=>x.includes("HttpOnly")&&x.includes("Secure")));
 assert.equal(clearAuthCookies(old,true).length,2);
 assert.throws(()=>rotateAuthCookies("x".repeat(8000),old,true),
  /OIDC_ENCRYPTED_SESSION_TOO_LARGE/);
});
