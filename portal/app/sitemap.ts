import type {MetadataRoute} from "next";
import {articles} from "../lib/content";
const routes=["/","/lieferantenboni-pruefen","/margenanalyse","/auftragsautomatisierung",
 "/serviceumsatz","/wissen","/preis-und-ablauf","/bonusstaffeln-pruefen",
 "/bonusgutschriften-abgleichen","/eignungscheck","/status"];
export default function sitemap():MetadataRoute.Sitemap {
 const base=process.env.NEXT_PUBLIC_SITE_URL;
 if(process.env.PUBLIC_LAUNCH_APPROVED!=="true" || !base)return [];
 return [...routes,...articles.map(a=>"/wissen/"+a.slug)].map(route=>({
   url:new URL(route,base).toString(),changeFrequency:"monthly" as const,priority:route==="/"?1:0.6
 }));
}
