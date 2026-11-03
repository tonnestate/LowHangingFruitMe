import type {Metadata} from "next";
import Link from "next/link";
import {PageIntro} from "../../components/PageIntro";
import {ConversionCTA} from "../../components/ConversionCTA";
export const metadata:Metadata={title:"Margenanalyse im Großhandel – Perspektive",description:"Geplante CFO-Margenkontrollen: Einkaufskostendrift, Rabatte und Kundenprofitabilität. Modul noch nicht produktiv verfügbar."};
export default function Margin(){return <><PageIntro eyebrow="CFO & Profit Intelligence" title="Margenabweichungen dort erkennen, wo sie entstehen." description="Margensteuerung verlangt den Vergleich von Einkaufskonditionen, Verkaufspreisen, Rabatten und tatsächlich gebuchten Beträgen. Dieses Prüfmodul befindet sich noch in der Konzeption." development/>
<section className="section divided-section"><div className="section-heading"><h2>Geplante Kontrollbereiche.</h2></div><div className="feature-grid">{[
["Preisabweichungen","Welche Kostenänderungen sind in die Verkaufskalkulation eingeflossen?"],
["Vertragsaktualität","Sind Preisvereinbarungen und Gültigkeitszeiträume korrekt hinterlegt?"],
["Rabattkontrollen","Lassen sich genehmigte und ungeklärte Abweichungen unterscheiden?"],
["Profitabilität","Welche Informationen wären für belastbare Deckungsbeitragsprüfungen erforderlich?"]
].map(([t,d])=><article key={t} className="feature-card"><h3>{t}</h3><p>{d}</p></article>)}</div></section>
<section className="section divided-section"><div className="section-heading"><h2>Was heute bereits existiert.</h2><p>Die vorhandene Python-Engine prüft bestimmte Lieferantenbonusmodelle. Das ist keine vollständige Margenanalyse.</p><Link className="button-secondary" href="/lieferantenboni-pruefen">Aktuellen technischen Produktkern ansehen</Link></div></section>
<ConversionCTA title="Zuerst die messbare Bonusprüfung – danach weitere CFO-Kontrollen."/></>}
