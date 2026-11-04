// The BFF must never buffer unbounded, untrusted upstream responses.
export class UpstreamLimitError extends Error {
 constructor(){super("upstream response exceeds the accepted byte budget");
  this.name="UpstreamLimitError";}
}
export function upstreamTimeoutMs(method,apiPath){
 // Docling's isolated worker has a hard 120s limit; leave 15s for API/BFF.
 return method==="POST"&&apiPath==="/v1/contract-candidates" ? 135000 : 45000;
}
export async function readBoundedResponse(response,maxBytes){
 if(!Number.isSafeInteger(maxBytes)||maxBytes<0)throw new TypeError("invalid byte limit");
 const declared=response.headers.get("content-length");
 if(declared!==null &&
    (!/^\d{1,16}$/.test(declared)||BigInt(declared)>BigInt(maxBytes)))
   throw new UpstreamLimitError();
 const reader=response.body?.getReader();
 if(!reader)return new ArrayBuffer(0);
 const parts=[];
 let length=0;
 try{
  while(true){
   const {value,done}=await reader.read();
   if(done)break;
   if(!(value instanceof Uint8Array))throw new TypeError("invalid upstream byte chunk");
   if(value.byteLength>maxBytes-length){
    try{await reader.cancel();}catch{}
    throw new UpstreamLimitError();
   }
   length+=value.byteLength;
   parts.push(value);
  }
 }finally{reader.releaseLock();}
 const result=new Uint8Array(length);
 let offset=0;
 for(const part of parts){result.set(part,offset);offset+=part.byteLength;}
 return result.buffer;
}
