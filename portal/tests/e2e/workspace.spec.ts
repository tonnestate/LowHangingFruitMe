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
 const billingId="12345678-1234-4abc-9def-123456789012";
 const billingGet=await request.get("/api/finance/billing-packets/"+billingId+
  "?tenant_id=TEST&legal_entity_id=TEST");
 expect([401,503]).toContain(billingGet.status());
 const billingPost=await request.post("/api/finance/audits/"+billingId+"/billing-packets",{
  data:{tenant_id:"TEST",legal_entity_id:"TEST"},
 });
 expect([401,403,503]).toContain(billingPost.status());
 const priorAudit=await request.get("/api/finance/audits/"+billingId+
  "?tenant_id=TEST&legal_entity_id=TEST");
 expect([401,503]).toContain(priorAudit.status());
});
