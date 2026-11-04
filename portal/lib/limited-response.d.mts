export class UpstreamLimitError extends Error {
 constructor();
}
export function readBoundedResponse(response:Response,maxBytes:number):Promise<ArrayBuffer>;
export function upstreamTimeoutMs(method:string,apiPath:string):number;
