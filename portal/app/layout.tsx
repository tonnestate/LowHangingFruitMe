import type {Metadata,Viewport} from "next";
import "./brand.generated.css";
import "./globals.css";
import {Header} from "../components/Header";
import {Footer} from "../components/Footer";

const base=process.env.NEXT_PUBLIC_SITE_URL;
const live=process.env.PUBLIC_LAUNCH_APPROVED==="true";
export const metadata:Metadata={
 title:{default:"LowHangingFruitMe | Finanzpotenziale nachvollziehbar prüfen",template:"%s | LowHangingFruitMe"},
 description:"Beleggestützte Prüfung von Lieferantenboni und Bonusgutschriften. Transparente 3-%-Erfolgsprovision als geplantes Pilotangebot.",
 robots:live?{index:true,follow:true}:{index:false,follow:false},
 metadataBase:base?new URL(base):undefined,
 openGraph:{type:"website",locale:"de_DE",siteName:"LowHangingFruitMe",images:[{url:"/neon-banner.png",alt:"LowHangingFruitMe Neon Markenbanner"}]},
};
export const viewport:Viewport={width:"device-width",initialScale:1};
export default function RootLayout({children}:{children:React.ReactNode}){
 return <html lang="de"><body><a href="#main" className="skip-link">Zum Inhalt springen</a><Header/><main id="main">{children}</main><Footer/></body></html>;
}
