import Link from "next/link";
export function Footer(){
 return <footer className="footer"><div className="footer-grid">
   <div><strong>LowHangingFruitMe</strong><p>Beleggestützte Finanzprüfung für den deutschen Mittelstand. Eigenständiges FruitStack-Produkt, aktuell in Pilotvorbereitung.</p></div>
   <nav aria-label="Footernavigation"><Link href="/lieferantenboni-pruefen">Lieferantenboni</Link><Link href="/preis-und-ablauf">Preis & Ablauf</Link><Link href="/wissen">Fachwissen</Link><Link href="/eignungscheck">Eignungscheck</Link></nav>
   <nav aria-label="Rechtliches"><Link href="/impressum">Impressum</Link><Link href="/datenschutz">Datenschutz</Link><Link href="/status">Produktstatus</Link></nav>
  </div><p className="footer-bottom">Keine Inkassoleistung, kein verbindlicher Anspruchsnachweis, keine behauptete SOC-2-Zertifizierung. © LowHangingFruitMe</p>
 </footer>;
}
