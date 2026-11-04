// Confidential server-only OIDC refresh and Auth.js session-cookie rotation.
// Never import in a Client Component. Token responses are not exposed in JSON.
import {createHash} from "node:crypto";

const MAX_TOKEN_RESPONSE=16*1024;
const COOKIE_CHUNK=3900;
const MAX_COOKIE_CHUNKS=2;
const inFlight=new Map();
const recent=new Map();

export function checkedTokenEndpoint(issuer,endpoint){
  if(typeof issuer!=="string"||typeof endpoint!=="string")throw new Error("OIDC_CONFIG_INVALID");
  let identity,token;
  try{identity=new URL(issuer);token=new URL(endpoint);}
  catch{throw new Error("OIDC_CONFIG_INVALID");}
  if(identity.protocol!=="https:"||token.protocol!=="https:"||
     identity.origin!==token.origin||identity.username||identity.password||
     token.username||token.password||identity.search||identity.hash||
     token.search||token.hash||token.pathname==="/"||
     !token.pathname.startsWith(identity.pathname.replace(/\/$/,"")+"/")){
    throw new Error("OIDC_CONFIG_INVALID");
  }
  return token.toString();
}

export function authCookieName(secure){
  if(typeof secure!=="boolean")throw new Error("OIDC_COOKIE_CONFIG_INVALID");
  return (secure?"__Secure-":"")+"authjs.session-token";
}

export function sessionCookieNames(existingCookies,secure){
  const name=authCookieName(secure);
  if(!Array.isArray(existingCookies))return [];
  return existingCookies.map(x=>x?.name).filter(x=>
    typeof x==="string"&&
    (x===name || (x.startsWith(name+".")&&
                 /^\d+$/.test(x.slice(name.length+1)))));
}

function serializeCookie(name,value,{secure,maxAge}){
  if(!/^[A-Za-z0-9_.-]+$/.test(name))throw new Error("OIDC_COOKIE_CONFIG_INVALID");
  return name+"="+value+"; Path=/; HttpOnly; SameSite=Lax; "+
         (secure?"Secure; ":"")+"Max-Age="+maxAge;
}

export function clearAuthCookies(existingCookies,secure){
  return sessionCookieNames(existingCookies,secure).map(name=>
    serializeCookie(name,"",{secure,maxAge:0})+
    "; Expires=Thu, 01 Jan 1970 00:00:00 GMT");
}

export function rotateAuthCookies(encodedJwt,existingCookies,secure){
  if(typeof encodedJwt!=="string"||!/^[A-Za-z0-9._-]+$/.test(encodedJwt)||
     encodedJwt.length<10||encodedJwt.length>COOKIE_CHUNK*MAX_COOKIE_CHUNKS){
    throw new Error("OIDC_ENCRYPTED_SESSION_TOO_LARGE");
  }
  const base=authCookieName(secure);
  const pieces=[];
  for(let i=0;i<encodedJwt.length;i+=COOKIE_CHUNK)pieces.push(encodedJwt.slice(i,i+COOKIE_CHUNK));
  const target=pieces.length===1?[base]:pieces.map((_,i)=>base+"."+i);
  const existing=sessionCookieNames(existingCookies,secure);
  const old=existing.filter(name=>!target.includes(name)).map(name=>
    serializeCookie(name,"",{secure,maxAge:0})+
    "; Expires=Thu, 01 Jan 1970 00:00:00 GMT");
  const updated=target.map((name,i)=>serializeCookie(name,pieces[i],{secure,maxAge:3600}));
  return [...old,...updated];
}

async function readBoundedJson(response){
  const declared=response.headers?.get?.("content-length");
  if(declared && (!/^\d+$/.test(declared)||Number(declared)>MAX_TOKEN_RESPONSE)){
    throw new Error("OIDC_REFRESH_REJECTED");
  }
  let bytes=[];
  let length=0;
  if(response.body&&typeof response.body.getReader==="function"){
    const reader=response.body.getReader();
    try{
      while(true){
        const {done,value}=await reader.read();
        if(done)break;
        length+=value.byteLength;
        if(length>MAX_TOKEN_RESPONSE)throw new Error("OIDC_REFRESH_REJECTED");
        bytes.push(Buffer.from(value));
      }
    }finally{reader.releaseLock();}
  }else{
    const text=await response.text();
    const raw=Buffer.from(text,"utf8");
    if(raw.length>MAX_TOKEN_RESPONSE)throw new Error("OIDC_REFRESH_REJECTED");
    bytes=[raw];
  }
  try{return JSON.parse(Buffer.concat(bytes).toString("utf8"));}
  catch{throw new Error("OIDC_REFRESH_REJECTED");}
}

export async function renewApiCredential({
  issuer,tokenEndpoint,clientId,clientSecret,refreshToken,
  fetcher=fetch,now=()=>Date.now(),
}){
  const endpoint=checkedTokenEndpoint(issuer,tokenEndpoint);
  if(typeof clientId!=="string"||!clientId||clientId.length>256||
     typeof clientSecret!=="string"||!clientSecret||
     typeof refreshToken!=="string"||!refreshToken||refreshToken.length>16384){
    throw new Error("OIDC_REFRESH_REJECTED");
  }
  const fingerprint=createHash("sha256").update(
    endpoint+"\n"+clientId+"\n"+refreshToken
  ).digest("hex");
  const current=now();
  for(const [key,item] of recent)if(item.until<=current)recent.delete(key);
  const cached=recent.get(fingerprint);
  if(cached&&cached.until>current)return cached.result;
  const shared=inFlight.get(fingerprint);
  if(shared)return shared;
  const attempt=(async()=>{
    try{
      const reply=await fetcher(endpoint,{
        method:"POST",redirect:"error",cache:"no-store",
        headers:{"Content-Type":"application/x-www-form-urlencoded",
                 "Accept":"application/json"},
        body:new URLSearchParams({
          grant_type:"refresh_token",client_id:clientId,
          client_secret:clientSecret,refresh_token:refreshToken,
        }),
        signal:AbortSignal.timeout(8000),
      });
      if(!reply.ok)throw new Error("OIDC_REFRESH_REJECTED");
      const data=await readBoundedJson(reply);
      if(!data || typeof data!=="object"||
         typeof data.access_token!=="string"||
         !data.access_token||data.access_token.length>8192||
         !Number.isInteger(data.expires_in)||
         data.expires_in<60||data.expires_in>3600||
         (data.token_type&&String(data.token_type).toLowerCase()!=="bearer")||
         (data.refresh_token!==undefined&&
          (typeof data.refresh_token!=="string"||
           !data.refresh_token||data.refresh_token.length>16384))){
        throw new Error("OIDC_REFRESH_REJECTED");
      }
      const issued=now();
      const result={
        accessToken:data.access_token,
        expiresAt:Math.floor(issued/1000)+data.expires_in,
        refreshToken:data.refresh_token||refreshToken,
      };
      recent.set(fingerprint,{result,until:issued+15000});
      if(recent.size>256){
        const oldest=recent.keys().next().value;
        if(oldest)recent.delete(oldest);
      }
      return result;
    }catch{
      throw new Error("OIDC_REFRESH_REJECTED");
    }
  })();
  inFlight.set(fingerprint,attempt);
  try{return await attempt;}
  finally{if(inFlight.get(fingerprint)===attempt)inFlight.delete(fingerprint);}
}
