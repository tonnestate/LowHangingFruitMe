/**
 * Fail closed on a public release if verified legal/operational information is
 * missing. This is NOT a substitute for an actual legal security review.
 */
const live=process.env.PUBLIC_LAUNCH_APPROVED==="true";
if (live) {
 const required=[
 "NEXT_PUBLIC_SITE_URL","SITE_OPERATOR_NAME","SITE_OPERATOR_ADDRESS",
 "SITE_OPERATOR_EMAIL","CONTACT_EMAIL","SITE_PRIVACY_NOTICE", "SITE_IMPRINT_EXTRA","LEGAL_CONTENT_REVIEWED",
 "DEPLOYMENT_SECURITY_APPROVED"
 ];
 const missing=required.filter(k=>!process.env[k]);
 if(missing.length)throw Error("Public launch blocked: missing "+missing.join(", "));
 if(process.env.LEGAL_CONTENT_REVIEWED!=="true"||process.env.DEPLOYMENT_SECURITY_APPROVED!=="true")
   throw Error("Public launch requires explicit reviewed legal and security approvals");
 if(process.env.SITE_PRIVACY_NOTICE.length<500 || process.env.SITE_IMPRINT_EXTRA.length<60)
   throw Error("Public launch blocked: real, reviewed legal text is required");
 if(!process.env.NEXT_PUBLIC_SITE_URL.startsWith("https://"))
   throw Error("Public launch needs a verified HTTPS site URL");
}
console.log(live?"Public launch flags provided; legal review still operator responsibility.":"Staging build only: robots disallow / noindex.");
