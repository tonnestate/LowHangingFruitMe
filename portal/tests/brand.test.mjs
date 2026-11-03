import test from "node:test";
import assert from "node:assert/strict";
import { existsSync,readFileSync } from "node:fs";
import { resolve } from "node:path";
import { createHash } from "node:crypto";
const root=resolve(process.cwd(),"..");
test("public brand asset matches original repository PNG exactly",()=>{
 const actual=readFileSync(resolve(root,"portal/public/neon-banner.png"));
 const original=readFileSync(resolve(root,"docs/Neon-Low-Hanging-FruitMe-Banner.png"));
 assert.equal(createHash("sha256").update(actual).digest("hex"),
              createHash("sha256").update(original).digest("hex"));
});
test("generated brand colors have pixel evidence and readable contrast",()=>{
 const file=resolve(root,"portal/public/brand-measurement.json");
 assert.ok(existsSync(file));
 const report=JSON.parse(readFileSync(file,"utf-8"));
 assert.ok(report.contrast_text_background>=4.5);
 assert.ok(report.tokens["--brand-primary"].source_pixel);
 assert.match(report.tokens["--brand-primary"].hex,/^#[0-9a-f]{6}$/);
});
