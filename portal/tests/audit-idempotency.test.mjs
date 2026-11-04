import test from "node:test";
import assert from "node:assert/strict";
import {auditIdempotencyKey} from "../lib/audit-idempotency.mjs";

test("same signed bundle has one stable replay key across browser retries",()=>{
 const a="12345678-1234-4abc-9def-123456789012";
 assert.equal(auditIdempotencyKey(a),a);
 assert.equal(auditIdempotencyKey(a),auditIdempotencyKey(a));
 assert.notEqual(auditIdempotencyKey("12345678-1234-4abc-9def-123456789013"),a);
});
test("unsigned, malformed and noncanonical bundle IDs cannot trigger an audit",()=>{
 for(const id of ["","../../etc/passwd","BUNDLE",null,undefined,
                  "12345678-1234-4ABC-9def-123456789012"]){
  assert.throws(()=>auditIdempotencyKey(id),/INVALID_SIGNED_BUNDLE_ID/);
 }
});
