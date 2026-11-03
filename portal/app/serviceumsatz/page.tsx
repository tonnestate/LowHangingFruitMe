import type {Metadata} from "next";
import {PageIntro} from "../../components/PageIntro";
import {ConversionCTA} from "../../components/ConversionCTA";
export const metadata:Metadata={title:"Serviceumsatz und Installed Base – Perspektive",description:"Geplantes Analysefeld für Wartungsverträge, Serviceintervalle und Gerätebasis; derzeit nicht produktiv."};
export default function Service(){return <><PageIntro eyebrow="Service Revenue · Konzept" title="Servicepotenziale aus bestehenden Kundenbeziehungen verstehen." description="Wartungsverträge, Wartungsintervalle und wiederkehrende Ersatzteilbedarfe könnten künftig auf belegbare Geschäftsvorfälle geprüft werden. Aktuell existiert dafür noch kein freigegebenes Produktmodul." development/>
<section className="section divided-section"><div className="section-heading"><h2>Perspektivische Anwendungsfälle.</h2></div><div className="feature-grid">{[
["Vertragsabdeckung","Welche installierten Geräte sind einem gültigen Servicevertrag zugeordnet?"],
["Ablaufhinweise","Welche Termine und Garantiefristen lassen sich aus einer belegten Basis ableiten?"],
["Ersatzteilbedarf","Wo fehlen belastbare Informationen für wiederkehrende Servicevorgänge?"],
["Umsatznachweis","Wie lässt sich ein tatsächlich zusätzlicher Erlös eindeutig zurechnen?"]
].map(([t,d])=><article className="feature-card" key={t}><h3>{t}</h3><p>{d}</p></article>)}</div></section>
<ConversionCTA title="Einfacher Einstieg über nachprüfbare Finanzkontrollen."/></>}
