/**
 * Uses the actual checked-in brand PNG, never an external image or guessed
 * brand HEX value. Generates CSS tokens + measured source-pixel evidence.
 */
import { readFileSync, writeFileSync, mkdirSync, copyFileSync } from "node:fs";
import { createHash } from "node:crypto";
import { fileURLToPath } from "node:url";
import { dirname, resolve, join } from "node:path";
import { PNG } from "pngjs";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
const portal = join(root, "portal");
const original = join(root, "docs/Neon-Low-Hanging-FruitMe-Banner.png");
const bytes = readFileSync(original);
const png = PNG.sync.read(bytes);
const hex = ([r,g,b]) => "#" + [r,g,b].map(n=>n.toString(16).padStart(2,"0")).join("");
const linear = v => {
  const c=v/255;
  return c<=0.04045?c/12.92:((c+0.055)/1.055)**2.4;
};
const lum = c => .2126*linear(c[0])+.7152*linear(c[1])+.0722*linear(c[2]);
const sat = c => {
  const mx=Math.max(...c), mn=Math.min(...c);
  return mx ? (mx-mn)/mx : 0;
};
const contrast = (a,b) => {
  const x=lum(a),y=lum(b);
  return (Math.max(x,y)+.05)/(Math.min(x,y)+.05);
};
// Bucket nearby pixels to avoid treating hundreds of gradient pixels as
// unrelated colors. Record an ORIGINAL representative pixel, not its bucket.
const buckets = new Map();
const step = Math.max(1,Math.floor(Math.sqrt(png.width*png.height/50000)));
for (let y=0;y<png.height;y+=step) for (let x=0;x<png.width;x+=step) {
  const i=(y*png.width+x)*4;
  if(png.data[i+3]<240)continue;
  const color=[png.data[i],png.data[i+1],png.data[i+2]];
  const bucket=color.map(v=>Math.floor(v/24)).join("-");
  const seen=buckets.get(bucket);
  if(seen)seen.count++;else buckets.set(bucket,{count:1,color,x,y});
}
const palette=[...buckets.values()].sort((a,b)=>b.count-a.count);
if(!palette.length)throw Error("PNG has no opaque brand pixels");
const pick=(predicate,fallback)=>palette.find(c=>predicate(c.color))??fallback;
const dark=pick(c=>lum(c)<.09,palette[0]);
const light=pick(c=>lum(c)>.73 && sat(c)<.23, [...palette].sort((a,b)=>lum(b.color)-lum(a.color))[0]);
const vivid=palette.filter(c=>sat(c.color)>.48 && lum(c)>.09 && lum(c)<.8);
const primary=vivid[0]??light;
const secondary=vivid.find(c=>Math.abs(lum(c.color)-lum(primary.color))>.13 && hex(c.color)!==hex(primary.color))??primary;
if(contrast(dark.color,light.color)<4.5)throw Error("Brand image does not provide readable dark/light pair");
const onAccent=contrast(primary.color,dark.color)>4.5?dark.color:light.color;
const vars={
  "--brand-background":dark,
  "--brand-text":light,
  "--brand-primary":primary,
  "--brand-secondary":secondary,
  "--brand-on-primary":{color:onAccent,x:null,y:null,count:null}
};
const css="/* Automatically measured from docs/Neon-Low-Hanging-FruitMe-Banner.png. */\n:root {\n"+
  Object.entries(vars).map(([name,item])=>"  "+name+": "+hex(item.color)+";").join("\n")+
  "\n}\n";
mkdirSync(join(portal,"public"),{recursive:true});
copyFileSync(original,join(portal,"public","neon-banner.png"));
writeFileSync(join(portal,"app","brand.generated.css"),css);
const report={
  source:"docs/Neon-Low-Hanging-FruitMe-Banner.png",
  sha256:createHash("sha256").update(bytes).digest("hex"),
  width:png.width,height:png.height,
  method:"PNG sRGB pixels sampled, 24-step RGB buckets, original representative pixel for each CSS token",
  contrast_text_background:Number(contrast(dark.color,light.color).toFixed(2)),
  tokens:Object.fromEntries(Object.entries(vars).map(([key,p])=>[key,{
    hex:hex(p.color),source_pixel:p.x===null?null:{x:p.x,y:p.y},sample_count:p.count
  }]))
};
writeFileSync(join(portal,"public","brand-measurement.json"),JSON.stringify(report,null,2)+"\n");
console.log("Brand tokens generated from actual repository image:",report.sha256,report.width+"x"+report.height);
