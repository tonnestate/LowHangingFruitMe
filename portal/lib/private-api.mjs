// Server-side BFF allowlist. No user-supplied URL or arbitrary proxy access.
const uuid="[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}";
const routes = {
  GET: [
    /^me$/,
    new RegExp("^uploads/"+uuid+"$"),
    new RegExp("^uploads/"+uuid+"/inspect$"),
    new RegExp("^uploads/"+uuid+"/invoice-preview$"),
    new RegExp("^audits/"+uuid+"$"),
    new RegExp("^audits/"+uuid+"/fee-ledger$"),
  ],
  POST: [
    /^uploads$/, /^bundles$/, /^audits$/,
    new RegExp("^audits/"+uuid+"/recovery-events$"),
    new RegExp("^recovery-events/"+uuid+"/review$"),
  ],
  PUT: [new RegExp("^uploads/"+uuid+"/content$")],
};
export function verifiedApiPath(method, segments) {
  if(!Array.isArray(segments) || segments.length<1 || segments.length>4 ||
     segments.some(s=>typeof s!=="string"||s.length>96))return null;
  const slug=segments.join("/");
  return (routes[method]??[]).some(re=>re.test(slug)) ? "/v1/"+slug : null;
}
export function trustedApiOrigin(value) {
  if(!value || typeof value!=="string")return null;
  try {
    const url=new URL(value);
    if(url.protocol!=="http:"||url.hostname!=="127.0.0.1"||
       url.username||url.password||url.search||url.hash||url.pathname!=="/"||
       !url.port || +url.port<1024 || +url.port>65535)return null;
    return url.origin;
  }catch{return null;}
}
export function sameOrigin(requestUrl, origin) {
  if(!origin)return false;
  try{return new URL(requestUrl).origin===new URL(origin).origin;}
  catch{return false;}
}
