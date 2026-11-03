import test from "node:test";
import assert from "node:assert/strict";
import { feePreview } from "../lib/fee.mjs";

test("5 percent of genuinely realized hypothetical net benefit",()=>{
 const v=feePreview("25000");
 assert.deepEqual(v,{input:"25.000,00 €",fee:"1.250,00 €",customer:"23.750,00 €"});
});
test("exact cent arithmetic, no binary floating point",()=>{
 const v=feePreview("0,50");
 assert.equal(v.fee,"0,03 €");
});
test("rejects invalid and very large unbounded numbers",()=>{
 assert.equal(feePreview("-100"),null);
 assert.equal(feePreview("1e20"),null);
 assert.equal(feePreview("1.2.3"),null);
 assert.equal(feePreview("9999999999999"),null);
});
