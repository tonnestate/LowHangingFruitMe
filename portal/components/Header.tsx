import Link from "next/link";
import {nav} from "../lib/content";

export function Header(){
 return <header className="site-header">
   <div className="header-inner">
    <Link className="wordmark" href="/" aria-label="LowHangingFruitMe Startseite"><span className="wordmark-dot" aria-hidden="true"/>LowHangingFruitMe</Link>
    <nav className="desktop-nav" aria-label="Hauptnavigation">{nav.map(n=><Link key={n.href} href={n.href}>{n.title}</Link>)}</nav>
    <Link className="header-cta" href="/eignungscheck">Eignungscheck</Link>
    <details className="mobile-nav"><summary>Menü <span aria-hidden="true">☰</span></summary>
      <nav aria-label="Mobile Hauptnavigation">{nav.map(n=><Link key={n.href} href={n.href}>{n.title}</Link>)}<Link href="/eignungscheck">Eignungscheck</Link></nav>
    </details>
   </div>
 </header>;
}
