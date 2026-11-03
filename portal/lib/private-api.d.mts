export function verifiedApiPath(method:string,segments:string[]):string|null;
export function trustedApiOrigin(value:string|undefined):string|null;
export function sameOrigin(requestUrl:string,origin:string|null):boolean;
