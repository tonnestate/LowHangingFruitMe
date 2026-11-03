import {cpSync, existsSync, mkdirSync} from "node:fs";
import {resolve} from "node:path";
// A Next.js standalone build does not automatically copy static/public.
const root=resolve(import.meta.dirname, "..");
const output=resolve(root,".next/standalone");
if(!existsSync(resolve(output,"server.js")))throw Error("Next standalone build missing");
mkdirSync(resolve(output,".next"),{recursive:true});
cpSync(resolve(root,".next/static"),resolve(output,".next/static"),{recursive:true,force:true});
cpSync(resolve(root,"public"),resolve(output,"public"),{recursive:true,force:true});
console.log("Standalone static and exact neon source banner packaged");
