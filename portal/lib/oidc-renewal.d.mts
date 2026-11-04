export function checkedTokenEndpoint(issuer:string,endpoint:string):string;
export function authCookieName(secure:boolean):string;
export function sessionCookieNames(
  existingCookies:Array<{name:string;value?:string}>,secure:boolean,
):string[];
export function clearAuthCookies(
  existingCookies:Array<{name:string;value?:string}>,secure:boolean,
):string[];
export function rotateAuthCookies(
  encodedJwt:string,existingCookies:Array<{name:string;value?:string}>,
  secure:boolean,
):string[];
export function renewApiCredential(args:{
  issuer:string;tokenEndpoint:string;clientId:string;clientSecret:string;
  refreshToken:string;fetcher?:typeof fetch;now?:()=>number;
}):Promise<{accessToken:string;expiresAt:number;refreshToken:string}>;
