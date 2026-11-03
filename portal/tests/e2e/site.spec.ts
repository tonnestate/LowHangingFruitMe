import {test,expect} from "@playwright/test";
test("homepage contains honest business claim, complete sections and original banner",async({page},testInfo)=>{
 await page.goto("/");
 await expect(page.locator("h1")).toContainText("Lieferantenvereinbarungen");
 const imageResponse=await page.request.get("/neon-banner.png");
 console.log("PNG route HTTP status",imageResponse.status(),"content-type",imageResponse.headers()["content-type"]);
 const imgInfo=await page.locator(".hero-media img").evaluate((img:HTMLImageElement)=>({
   complete:img.complete,naturalWidth:img.naturalWidth,naturalHeight:img.naturalHeight,
   width:img.getBoundingClientRect().width,height:img.getBoundingClientRect().height,
   parentWidth:img.parentElement?.getBoundingClientRect().width
 }));
 console.log("Banner browser dimensions",JSON.stringify(imgInfo));
 expect(imageResponse.ok()).toBeTruthy();
 await expect(page.getByAltText("Originales Neon-Low-Hanging-FruitMe-Markenbanner")).toBeVisible();
 await expect(page.getByText("Sieben mögliche Prüffelder. Ein klarer Start.")).toBeVisible();
 await expect(page.getByText("3 %", {exact:false}).first()).toBeVisible();
 await page.screenshot({path:"test-results/home-"+testInfo.project.name+".png",fullPage:true});
});
test("responsive navigation and FAQ are functional",async({page},testInfo)=>{
 await page.goto("/");
 if(testInfo.project.name==="mobile-390" || testInfo.project.name==="tablet-768"){
  await page.locator(".mobile-nav summary").click();
  await expect(page.locator(".mobile-nav nav").getByRole("link",{name:"Lieferantenboni"})).toBeVisible();
 }else{
  await expect(page.locator(".desktop-nav").getByRole("link",{name:"Lieferantenboni"})).toBeVisible();
 }
 const question=page.locator("#faq details").first();
 await question.locator("summary").click();
 await expect(question.locator("p")).toBeVisible();
});
test("fee preview is exact and not disguised as real audit",async({page})=>{
 await page.goto("/preis-und-ablauf");
 const amount=page.getByLabel("Zusätzlich realisierter Nettobetrag in €");
 await amount.fill("10000");
 await expect(page.locator(".calc-results")).toContainText("300,00 €");
 await expect(page.locator(".calc-results")).toContainText("9.700,00 €");
 await expect(page.getByText("Das ist keine Prognose")).toBeVisible();
});
test("nonexistent pages return real 404, staging remains noindex",async({page,request})=>{
 const absent=await request.get("/wissen/nicht-existierender-artikel");
 expect(absent.status()).toBe(404);
 const robots=await request.get("/robots.txt");
 expect(await robots.text()).toContain("Disallow: /");
 await page.goto("/lieferantenboni-pruefen");
 await expect(page.locator('meta[name="robots"]')).toHaveAttribute("content",/noindex/);
});
