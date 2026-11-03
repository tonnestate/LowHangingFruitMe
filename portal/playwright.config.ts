import {defineConfig,devices} from "@playwright/test";
export default defineConfig({
 testDir:"./tests/e2e",
 timeout:30000,
 retries:1,
 reporter:"list",
 use:{baseURL:"http://127.0.0.1:3107",trace:"retain-on-failure"},
 projects:[
   {name:"desktop-1440",use:{...devices["Desktop Chrome"],viewport:{width:1440,height:900}}},
   {name:"tablet-768",use:{...devices["Desktop Chrome"],viewport:{width:768,height:1024}}},
   {name:"mobile-390",use:{...devices["Desktop Chrome"],viewport:{width:390,height:844}}}
 ],
 webServer:{
   command:"npm run start:standalone",
   url:"http://127.0.0.1:3107",
   reuseExistingServer:!process.env.CI,
   timeout:60000
 }
});
