// One signed reviewed bundle identifies one financial audit execution.
// Never generate a fresh key on browser retry or after a network timeout.
const UUID=/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/;
export function auditIdempotencyKey(bundleId){
 if(typeof bundleId!=="string"||!UUID.test(bundleId))
  throw new Error("INVALID_SIGNED_BUNDLE_ID");
 return bundleId;
}
