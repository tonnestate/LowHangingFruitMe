import Link from "next/link";
import {AgentExplorer} from "../components/AgentExplorer";
import {FeeCalculator} from "../components/FeeCalculator";
import {ConversionCTA} from "../components/ConversionCTA";
import {articles} from "../lib/content";

const steps=[
 ["01","Daten verstehen","Vertragsunterlagen, Einkaufslisten und Gutschriften werden einem Lieferanten und einer Periode zugeordnet."],
 ["02","Regeln freigeben","Die Berechnungsregel wird aus der dokumentierten Vereinbarung abgeleitet und kontrolliert freigegeben."],
 ["03","Differenzen belegen","Das System vergleicht erwartete und erfasste Vergütungen und bewahrt die Quellenbezüge."],
 ["04","Realisierung prüfen","Erst tatsächlich zusätzlich zugeflossene oder wirksam verrechnete Beträge können die Honorargrundlage bilden."]
];
const industries=["Elektrogroßhandel","SHK & Gebäudetechnik","Industriebedarf / MRO","Baustoffhandel","Lebensmittelgroßhandel","Kfz-Teile","Verpackung & Hygiene","Spezialgroßhandel"];
const faqs=[
 ["Muss unser ERP ausgetauscht werden?","Nein. Der technische Import kann bereits bestimmte CSV- und Excel-Exporte nach geprüftem Mapping verarbeiten. Native ERP-Connectoren und ein öffentlicher Upload sind noch in Entwicklung."],
 ["Welche Daten braucht die Bonusprüfung?","Die konkrete Vertragsfassung, die vollständigen relevanten Einkaufsdaten der Abrechnungsperiode, vorhandene Bonusgutschriften, Retouren und getrennte ERP-Kontrollsummen."],
 ["Worauf beziehen sich die 5 %?","Das geplante Honorar bezieht sich ausschließlich auf nachgewiesene, zusätzlich zurechenbare und tatsächlich realisierte Nettobeträge. Eine bloß errechnete Differenz reicht nicht."],
 ["Übernimmt LowHangingFruitMe den Einzug?","Nein. Wir bieten keine eigenständige Rechtsvertretung oder Inkassoleistung. Der Kunde entscheidet über die weitere kaufmännische Klärung."],
 ["Was passiert mit vertraulichen Finanzdaten?","Aktuell gibt es auf dieser öffentlichen Website keinen Dokumentenupload. Ein geschützter Upload wird erst nach Sicherheits- und Datenschutzabnahme freigeschaltet."],
 ["Sind weitere Finanzmodule schon verfügbar?","Noch nicht. Nur der technische Rechenkern für bestimmte Lieferantenboni ist umgesetzt; die anderen Bereiche sind Entwicklungsziele."]
];
export default function Home(){
 return <>
 <section className="main-container hero">
  <div><span className="eyebrow">Financial Recovery · Pilotvorbereitung</span>
   <h1>Mehr aus Ihren Lieferantenvereinbarungen herausholen.</h1>
   <p className="hero-lead">Lieferantenboni, Einkaufsumsätze und erhaltene Gutschriften nachvollziehbar abgleichen. Damit mögliche Differenzen nicht zwischen Verträgen und Buchhaltung untergehen.</p>
   <div className="hero-actions"><Link className="button-primary" href="/lieferantenboni-pruefen">Lieferantenboni prüfen</Link><Link className="button-secondary" href="/preis-und-ablauf">5-%-Modell verstehen</Link></div>
   <div className="trust-line"><span>ERP-unabhängiger Datenexport</span><span>Nachvollziehbare Rechenregeln</span><span>Keine ERP-Schreibzugriffe</span></div>
  </div>
  <div className="hero-media"><img src="/neon-banner.png" alt="Originales Neon-Low-Hanging-FruitMe-Markenbanner" loading="eager"/><div className="image-caption">Eigenständige Finanzanalyse – kein ERP-Ersatz. Produkt derzeit in Pilotvorbereitung.</div></div>
 </section>
 <section className="section divided-section" id="ablauf">
  <div className="section-heading"><span className="eyebrow">So soll die Prüfung funktionieren</span><h2>Aus Daten werden prüfbare Hinweise.</h2>
   <p>Die Beträge stammen aus eindeutigen Vertragsregeln und verknüpften Buchungen, nicht aus einer erfundenen KI-Prognose.</p></div>
  <div className="step-grid">{steps.map(s=><article className="step-card" key={s[0]}><span className="step-num">{s[0]}</span><h3>{s[1]}</h3><p>{s[2]}</p></article>)}</div>
  <p className="note">Der vollständige digitale Kundenprozess ist noch nicht freigeschaltet. Einzelne Komponenten sind in der Python-Engine umgesetzt.</p>
 </section>
 <AgentExplorer/>
 <FeeCalculator/>
 <section className="section divided-section" id="branchen">
  <div className="section-heading"><span className="eyebrow">Für welche Unternehmen?</span><h2>Besonders relevant bei komplexen Lieferantenkonditionen.</h2><p>Entscheidend sind vorhandene Bonusvereinbarungen und prüfbare Einkaufsdaten – nicht die bloße Unternehmensgröße.</p></div>
  <div className="industry-grid">{industries.map(i=><div className="industry-card" key={i}>{i}</div>)}</div>
 </section>
 <section className="section divided-section faq" id="faq">
  <div><span className="eyebrow">Häufige Fragen</span><h2>Ein prüfbarer Ansatz statt großer Versprechen.</h2></div>
  <div>{faqs.map(([q,a])=><details key={q}><summary>{q}</summary><p>{a}</p></details>)}</div>
 </section>
 <section className="section divided-section"><div className="section-heading"><span className="eyebrow">Wissen</span><h2>Finanzkontrollen verständlich erklärt.</h2></div>
  <div className="article-grid">{articles.slice(0,2).map(a=><article className="article-tile" key={a.slug}>
   <span className="eyebrow">{a.category}</span><h3><Link href={"/wissen/"+a.slug}>{a.title}</Link></h3><p>{a.description}</p></article>)}</div>
 </section>
 <ConversionCTA/>
 </>;
}
