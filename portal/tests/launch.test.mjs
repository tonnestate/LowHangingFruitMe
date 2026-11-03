import test from "node:test";
import assert from "node:assert/strict";
import {spawnSync} from "node:child_process";
import {resolve} from "node:path";
const script=resolve("scripts/verify-launch.mjs");
test("staging can build without pretending legal approval",()=>{
 const r=spawnSync(process.execPath,[script],{encoding:"utf-8",
   env:{...process.env,PUBLIC_LAUNCH_APPROVED:"false"}});
 assert.equal(r.status,0,r.stderr);
});
test("public launch fails without real legal texts",()=>{
 const env={...process.env,
  PUBLIC_LAUNCH_APPROVED:"true",NEXT_PUBLIC_SITE_URL:"https://example.invalid",
  SITE_OPERATOR_NAME:"Sample",SITE_OPERATOR_ADDRESS:"Sample road",
  SITE_OPERATOR_EMAIL:"contact@example.invalid",CONTACT_EMAIL:"contact@example.invalid",
  LEGAL_CONTENT_REVIEWED:"true",DEPLOYMENT_SECURITY_APPROVED:"true",
  SITE_PRIVACY_NOTICE:"short",SITE_IMPRINT_EXTRA:"brief"
 };
 const r=spawnSync(process.execPath,[script],{encoding:"utf-8",env});
 assert.notEqual(r.status,0);
 assert.match(r.stderr,/real, reviewed legal text/);
});
