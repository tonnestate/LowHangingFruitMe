import type {Metadata} from "next";
import Link from "next/link";
import {PageIntro} from "../../components/PageIntro";
import {ConversionCTA} from "../../components/ConversionCTA";
export const metadata:Metadata={title:"Lieferantenboni prüfen lassen",description:"Jahresboni, Staffelvereinbarungen und gebuchte Gutschriften systematisch abgleichen. Quellengebundene Berechnung, 5 % geplante Erfolgsprovision."};
const reasons=[
 ["Vertragsstaffeln","Eine rückwirkend geltende Staffel kann zu einer anderen Vergütung führen als eine nur für die überschrittene Umsatzscheibe geltende Staffel."],
 ["Nicht zugeordnete Gutschriften","Gutschriften müssen nach Lieferant, Vertrag und Periode korrekt einer Bonusregel zugewiesen sein."],
 ["Retouren und Stornierungen","Die anrechenbare Basis verändert sich, wenn nachträgliche Korrekturen fehlen oder doppelt berücksichtigt werden."],
 ["Unvollständige Datenperioden","Ein Jahresbonus lässt sich nicht allein aus einem beliebigen Quartalsexport zuverlässig ableiten."]
];
export default function Rebate(){
return <><PageIntro eyebrow="Lieferantenbonus-Prüfung · Produktkern in Pilotvorbereitung"
 title="Sind Ihre vereinbarten Lieferantenboni vollständig angekommen?"
 description="Ein Vertrag nennt die Konditionen. Ihre Buchhaltung zeigt die Gutschriften. LowHangingFruitMe führt beide Perspektiven zu einer belegbaren Differenzprüfung zusammen – ohne selbst in Ihr ERP zu buchen."/>
 <section className="section divided-section"><div className="section-heading"><span className="eyebrow">Mögliche Differenzursachen</span><h2>Vier typische Kontrollfragen.</h2></div>
  <div className="feature-grid">{reasons.map(([title,description])=><article className="feature-card" key={title}><h3>{title}</h3><p>{description}</p></article>)}</div></section>
 <section className="section divided-section"><div className="section-heading"><span className="eyebrow">Datenanforderung</span><h2>Ein abgeschlossener Fall als Ausgangspunkt.</h2><p>Wir benötigen den relevanten Lieferantenvertrag einschließlich Nachträgen, die vollständigen relevanten Einkaufsbuchungen, erhaltene Gutschriften und gesonderte ERP-Kontrollsummen.</p></div>
  <div className="two-col"><div className="info-block"><h3>Strukturierte ERP-Daten</h3><p>CSV- oder XLSX-Export mit Buchungsreferenzen, Lieferant, Datum, Nettobetrag, Status und Rückgaben. Die Zuordnung wird kontrolliert bestätigt.</p></div><div className="info-block"><h3>Unstrukturierte Vertragsdaten</h3><p>PDF/DOCX und gegebenenfalls strukturierte E-Rechnungen. Die vollständige automatisierte Verarbeitung und der geschützte Kunden-Upload sind noch nicht freigeschaltet.</p></div></div>
 </section>
 <section className="section divided-section"><div className="section-heading"><span className="eyebrow">Prüfablauf</span><h2>Abgleichen statt schätzen.</h2></div>
  <div className="step-grid">{[
   ["01","Erfassen","Quellformate identifizieren, Lieferant, Zeitraum und Vertragsfassung klären."],
   ["02","Rekonstruieren","Freigegebene Bonusregel und zugehörige Einkaufsbasis dokumentieren."],
   ["03","Vergleichen","Erwarteten Bonus mit zugeordneten Buchungen und Gutschriften abgleichen."],
   ["04","Belegen","Abweichung mit Quellenreferenzen bereitstellen; wirtschaftliche Realisierung separat nachverfolgen."]
  ].map(([n,t,d])=><article className="step-card" key={n}><span className="step-num">{n}</span><h3>{t}</h3><p>{d}</p></article>)}</div>
  <p className="note">Bisher ist dieser Ablauf als Python-Kern mit synthetischen Fällen getestet, nicht als öffentlich nutzbarer Kundenprozess. Es werden keine Rechtsansprüche festgestellt oder Lieferanten autonom kontaktiert.</p>
 </section>
 <section className="section divided-section"><div className="section-heading"><span className="eyebrow">Vertiefen</span><h2>Welche Abweichung möchten Sie verstehen?</h2></div>
 <div className="feature-grid"><article className="feature-card"><h3><Link href="/bonusstaffeln-pruefen">Bonusstaffeln prüfen</Link></h3><p>Rückwirkende und marginale Staffelmodelle unterscheiden.</p></article>
 <article className="feature-card"><h3><Link href="/bonusgutschriften-abgleichen">Bonusgutschriften abgleichen</Link></h3><p>Buchungen und Vertragsperioden nachvollziehbar zuordnen.</p></article></div></section>
 <ConversionCTA title="Ein Lieferant. Eine Abrechnungsperiode. Ein nachvollziehbarer Prüfgegenstand."/>
</>;
}
