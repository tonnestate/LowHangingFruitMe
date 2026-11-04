import type { NextRequest } from "next/server";
import { getToken, encode } from "next-auth/jwt";
import {authCookieName, sessionCookieNames, clearAuthCookies,
        rotateAuthCookies, renewApiCredential} from "../../../../lib/oidc-renewal.mjs";
import { sameOrigin, trustedApiOrigin, verifiedApiPath } from "../../../../lib/private-api.mjs";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

type Context = {params: Promise<{segments:string[]}>};
const json = (code:number, error:string) => Response.json(
  {code:error},{status:code,headers:{"Cache-Control":"no-store"}},
);
const MAX_FILE = 16 * 1024 * 1024;
const MAX_JSON = 128 * 1024;

function withSessionCookies(response:Response,cookies:string[]):Response{
  for(const cookie of cookies)response.headers.append("Set-Cookie",cookie);
  return response;
}

async function limitedBody(request:NextRequest,limit:number):Promise<Uint8Array|null>{
  const reader=request.body?.getReader();
  if(!reader)return null;
  const bytes:Uint8Array[]=[];
  let size=0;
  try{
    while(true){
      const {value,done}=await reader.read();
      if(done)break;
      size+=value.byteLength;
      if(size>limit){await reader.cancel();return null;}
      bytes.push(value);
    }
  }finally{reader.releaseLock();}
  const output=new Uint8Array(size);
  let offset=0;
  for(const chunk of bytes){output.set(chunk,offset);offset+=chunk.byteLength;}
  return output;
}

async function forward(request:NextRequest,ctx:Context){
  const method=request.method;
  const {segments}=await ctx.params;
  const apiPath=verifiedApiPath(method,segments);
  if(!apiPath)return json(404,"UNKNOWN_PRIVATE_ROUTE");
  const configured=trustedApiOrigin(process.env.LHFM_API_INTERNAL_URL);
  if(!configured)return json(503,"BACKEND_NOT_CONFIGURED");
  const secret=process.env.AUTH_SECRET;
  const publicUrl=process.env.AUTH_URL;
  if(!secret||Buffer.byteLength(secret,"utf8")<32||
     !process.env.AUTH_OIDC_ISSUER||!process.env.AUTH_OIDC_TOKEN_ENDPOINT||
     !process.env.AUTH_OIDC_CLIENT_ID||!process.env.AUTH_OIDC_CLIENT_SECRET||
     !publicUrl?.startsWith("https://")){
    return json(503,"OIDC_NOT_CONFIGURED");
  }
  if(method!=="GET"&&!sameOrigin(publicUrl,request.headers.get("origin")))
    return json(403,"ORIGIN_FORBIDDEN");

  // Auth.js v5 uses Secure-prefixed cookies for the public HTTPS origin.
  // Do not infer this from request.nextUrl (Apache may proxy over HTTP).
  const secureCookie=true;
  const existingCookies=request.cookies.getAll();
  const existingSession=sessionCookieNames(existingCookies,secureCookie);
  if(!existingSession.length)return json(401,"AUTH_REQUIRED");

  let bearer:string|undefined;
  let rotatedCookies:string[]=[];
  try{
    const token=await getToken({req:request,secret,secureCookie});
    if(!token)throw new Error("AUTH_REQUIRED");
    const expires=token.apiExpiresAt;
    if(typeof token.apiAccessToken==="string" && token.apiAccessToken &&
       typeof expires==="number" && expires>Math.floor(Date.now()/1000)+45){
      bearer=token.apiAccessToken;
    }else{
      if(typeof token.apiRefreshToken!=="string"||!token.apiRefreshToken){
        throw new Error("SESSION_REAUTH_REQUIRED");
      }
      const renewed=await renewApiCredential({
        issuer:process.env.AUTH_OIDC_ISSUER,
        tokenEndpoint:process.env.AUTH_OIDC_TOKEN_ENDPOINT,
        clientId:process.env.AUTH_OIDC_CLIENT_ID,
        clientSecret:process.env.AUTH_OIDC_CLIENT_SECRET,
        refreshToken:token.apiRefreshToken,
      });
      const updated={...token,
        apiAccessToken:renewed.accessToken,
        apiExpiresAt:renewed.expiresAt,
        apiRefreshToken:renewed.refreshToken,
      };
      // Auth.js JWE with the exact cookie-name salt used by getToken().
      const name=authCookieName(secureCookie);
      const encrypted=await encode({token:updated,secret,salt:name,maxAge:3600});
      rotatedCookies=rotateAuthCookies(encrypted,existingCookies,secureCookie);
      bearer=renewed.accessToken;
    }
  }catch{
    return withSessionCookies(json(401,"SESSION_REAUTH_REQUIRED"),
                              clearAuthCookies(existingCookies,secureCookie));
  }
  if(!bearer)return json(401,"AUTH_REQUIRED");
  const fail=(code:number,error:string)=>withSessionCookies(json(code,error),rotatedCookies);
  const url=new URL(apiPath,configured);
  const allowedQuery=new Set(["tenant_id","legal_entity_id","dataset","sheet_name"]);
  for(const [key,value] of request.nextUrl.searchParams){
    if(!allowedQuery.has(key)||value.length>128)return fail(400,"INVALID_QUERY");
    url.searchParams.append(key,value);
  }
  const headers:Record<string,string>={"Authorization":"Bearer "+bearer};
  const idempotency=request.headers.get("Idempotency-Key");
  if(idempotency && /^[a-f0-9-]{36}$/.test(idempotency))headers["Idempotency-Key"]=idempotency;

  let body:Uint8Array|undefined;
  if(method==="POST"||method==="PUT"){
    const isBinary=method==="PUT";
    const contentType=request.headers.get("content-type")?.split(";",1)[0];
    if(contentType!==(isBinary?"application/octet-stream":"application/json"))
      return fail(415,"INVALID_CONTENT_TYPE");
    const limit=isBinary?MAX_FILE:MAX_JSON;
    const declared=request.headers.get("content-length");
    if(declared && (!/^\d+$/.test(declared)||+declared>limit))
      return fail(413,"REQUEST_TOO_LARGE");
    body=await limitedBody(request,limit)??undefined;
    if(!body)return fail(413,"REQUEST_TOO_LARGE");
    headers["Content-Type"]=isBinary?"application/octet-stream":"application/json";
  }
  try{
    const upstream=await fetch(url,{
      method,headers,body:body?Buffer.from(body):undefined,
      cache:"no-store",signal:AbortSignal.timeout(45000),
      redirect:"error",
    });

    if(/\/report\.(pdf|xlsx|json)$/.test(apiPath) && upstream.ok){
      const size=Number(upstream.headers.get("content-length")||"0");
      if(size>4*1024*1024)return fail(502,"REPORT_TOO_LARGE");
      const bytes=await upstream.arrayBuffer();
      if(bytes.byteLength>4*1024*1024)return fail(502,"REPORT_TOO_LARGE");
      const fmt=apiPath.split(".").at(-1);
      const kind=fmt==="pdf"?"application/pdf":
       fmt==="xlsx"?"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
       "application/json; charset=utf-8";
      const match=/\/audits\/([0-9a-f-]{36})\/report\./.exec(apiPath);
      if(!match)return fail(502,"INVALID_REPORT_RESPONSE");
      return withSessionCookies(new Response(bytes,{status:upstream.status,headers:{
        "Content-Type":kind,"Cache-Control":"no-store",
        "X-Content-Type-Options":"nosniff",
        "Content-Disposition":'attachment; filename="lhfm-'+match[1]+"."+fmt+'"',
      }}),rotatedCookies);
    }
    const result=await upstream.text();
    if(result.length>4*1024*1024)return fail(502,"UPSTREAM_RESPONSE_TOO_LARGE");
    return withSessionCookies(new Response(result,{
      status:upstream.status,
      headers:{"Content-Type":"application/json; charset=utf-8",
               "Cache-Control":"no-store",
               "X-Content-Type-Options":"nosniff"},
    }),rotatedCookies);
  }catch{return withSessionCookies(json(503,"BACKEND_UNAVAILABLE"),rotatedCookies);}
}
export async function GET(req:NextRequest,ctx:Context){return forward(req,ctx);}
export async function POST(req:NextRequest,ctx:Context){return forward(req,ctx);}
export async function PUT(req:NextRequest,ctx:Context){return forward(req,ctx);}
