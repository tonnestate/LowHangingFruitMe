import {test,expect} from "@playwright/test";
test("protected workplace blocks uploads when no identity service is configured",async({page,request})=>{
 await page.goto("/arbeitsplatz");
 await expect(page.locator("h1")).toContainText("Unternehmenszugang");
 await expect(page.getByText("nimmt die Website keine Finanzdaten")).toBeVisible();
 const get=await request.get("/api/finance/me?tenant_id=TEST&legal_entity_id=TEST");
 expect([401,503]).toContain(get.status());
 const post=await request.post("/api/finance/uploads",{
   data:{tenant_id:"TEST",legal_entity_id:"TEST",kind:"ERP_CSV",
     byte_size:10,sha256:"0".repeat(64)},
 });
 expect([401,403,503]).toContain(post.status());
});
