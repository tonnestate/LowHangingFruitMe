import type { NextRequest } from "next/server";
import { getToken } from "next-auth/jwt";
import { sameOrigin, trustedApiOrigin, verifiedApiPath } from "../../../../lib/private-api.mjs";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

type Context = {params: Promise<{segments:string[]}>};
const json = (code:number, error:string) => Response.json(
  {code:error},{status:code,headers:{"Cache-Control":"no-store"}},
);
const MAX_FILE = 16 * 1024 * 1024;
const MAX_JSON = 128 * 1024;

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
  if(!process.env.AUTH_SECRET || !process.env.AUTH_OIDC_ISSUER)return json(503,"OIDC_NOT_CONFIGURED");
  if(method!=="GET"&&!sameOrigin(request.url,request.headers.get("origin")))
    return json(403,"ORIGIN_FORBIDDEN");

  let bearer:string|undefined;
  try{
    const token=await getToken({req:request,secret:process.env.AUTH_SECRET,
      secureCookie:request.nextUrl.protocol==="https:"});
    if(token && typeof token.apiAccessToken==="string" &&
       typeof token.apiExpiresAt==="number" &&
       token.apiExpiresAt>Math.floor(Date.now()/1000)+10){
      bearer=token.apiAccessToken;
    }
  }catch{
    return json(401,"AUTH_REQUIRED");
  }
  if(!bearer)return json(401,"AUTH_REQUIRED");
  const url=new URL(apiPath,configured);
  const allowedQuery=new Set(["tenant_id","legal_entity_id","dataset","sheet_name"]);
  for(const [key,value] of request.nextUrl.searchParams){
    if(!allowedQuery.has(key)||value.length>128)return json(400,"INVALID_QUERY");
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
      return json(415,"INVALID_CONTENT_TYPE");
    const limit=isBinary?MAX_FILE:MAX_JSON;
    const declared=request.headers.get("content-length");
    if(declared && (!/^\d+$/.test(declared)||+declared>limit))
      return json(413,"REQUEST_TOO_LARGE");
    body=await limitedBody(request,limit)??undefined;
    if(!body)return json(413,"REQUEST_TOO_LARGE");
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
      if(size>4*1024*1024)return json(502,"REPORT_TOO_LARGE");
      const bytes=await upstream.arrayBuffer();
      if(bytes.byteLength>4*1024*1024)return json(502,"REPORT_TOO_LARGE");
      const fmt=apiPath.split(".").at(-1);
      const kind=fmt==="pdf"?"application/pdf":
       fmt==="xlsx"?"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
       "application/json; charset=utf-8";
      const match=/\/audits\/([0-9a-f-]{36})\/report\./.exec(apiPath);
      if(!match)return json(502,"INVALID_REPORT_RESPONSE");
      return new Response(bytes,{status:upstream.status,headers:{
        "Content-Type":kind,"Cache-Control":"no-store",
        "X-Content-Type-Options":"nosniff",
        "Content-Disposition":'attachment; filename="lhfm-'+match[1]+"."+fmt+'"',
      }});
    }
    const result=await upstream.text();
    if(result.length>4*1024*1024)return json(502,"UPSTREAM_RESPONSE_TOO_LARGE");
    return new Response(result,{
      status:upstream.status,
      headers:{"Content-Type":"application/json; charset=utf-8",
               "Cache-Control":"no-store",
               "X-Content-Type-Options":"nosniff"},
    });
  }catch{return json(503,"BACKEND_UNAVAILABLE");}
}
export async function GET(req:NextRequest,ctx:Context){return forward(req,ctx);}
export async function POST(req:NextRequest,ctx:Context){return forward(req,ctx);}
export async function PUT(req:NextRequest,ctx:Context){return forward(req,ctx);}
