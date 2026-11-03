import type {Metadata} from "next";
import {PageIntro} from "../../components/PageIntro";
import {ConversionCTA} from "../../components/ConversionCTA";
export const metadata:Metadata={title:"Bonusgutschriften abgleichen",description:"Lieferantengutschriften mit Bonusvereinbarung, Lieferant, Zeitraum und Buchungsbelegen abgleichen."};
export default function Credits(){return <><PageIntro eyebrow="Fachthema Gutschriften" title="Eine Gutschrift ist nur dann aussagekräftig, wenn sie richtig zugeordnet ist." description="Lieferant, Vertrag und Abrechnungsperiode müssen zusammenpassen. Nur dann lässt sich die bereits erhaltene Vergütung sinnvoll mit der vertraglich berechneten Erwartung vergleichen."/>
<section className="section divided-section"><div className="section-heading"><h2>Welche Informationen zusammengehören.</h2></div><div className="feature-grid">{[
["Lieferanten-ID","Dasselbe Unternehmen kann unter mehreren Buchungsschlüsseln geführt werden."],
["Vertragsreferenz","Gutschriften mehrerer Bonusprogramme dürfen nicht vermischt werden."],
["Vertragsperiode","Eine spätere Buchung kann sich auf ein früheres Bonusjahr beziehen."],
["Korrekturen","Storno, Rückgabe und doppelte Buchung müssen nachvollziehbar behandelt werden."]
].map(([t,d])=><article className="feature-card" key={t}><h3>{t}</h3><p>{d}</p></article>)}</div></section>
<ConversionCTA/></>}
