import type {MetadataRoute} from "next";
export default function robots():MetadataRoute.Robots {
 const live=process.env.PUBLIC_LAUNCH_APPROVED==="true";
 return {rules:live?{userAgent:"*",allow:"/"}:{userAgent:"*",disallow:"/"},
   sitemap:live&&process.env.NEXT_PUBLIC_SITE_URL?process.env.NEXT_PUBLIC_SITE_URL+"/sitemap.xml":undefined};
}
