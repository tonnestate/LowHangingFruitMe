import type {Metadata} from "next";
import {PageIntro} from "../../components/PageIntro";
import {FeeCalculator} from "../../components/FeeCalculator";
import {ConversionCTA} from "../../components/ConversionCTA";
export const metadata:Metadata={title:"Preis und Ablauf – 3 % Erfolgsprovision",description:"LowHangingFruitMe plant 3 % Erfolgsprovision ausschließlich auf nachweislich zusätzlich realisierte Nettobeträge. Keine Grundgebühr."};
export default function Price(){return <><PageIntro eyebrow="Geplantes Pilotangebot" title="97 % des zusätzlichen Nettoerfolgs bleiben beim Kunden." description="Das vorgesehene Preismodell: keine Grundgebühr, keine Einrichtungsgebühr, 3 % ausschließlich auf nachweislich zusätzliche, ursächlich zurechenbare und tatsächlich realisierte Nettobeträge."/>
<FeeCalculator/>
<section className="section divided-section"><div className="section-heading"><h2>Wann entsteht überhaupt ein Honorar?</h2><p>Eine rechnerische Abweichung ist noch kein wirtschaftlicher Erfolg. Deshalb müssen berechneter Bonus, vorhandene Gutschriften, späterer Zufluss und Honorar getrennt verfolgt werden.</p></div>
<div className="step-grid">{[
["01","Prüfgegenstand","Vertrag, Lieferant, Zeitraum und zulässige Daten festlegen."],
["02","Differenz","Reproduzierbare Berechnung und Datenqualität dokumentieren."],
["03","Realisierung","Zusätzliche Zahlung oder wirksame Verrechnung eindeutig nachweisen."],
["04","Abrechnung","Nur die zurechenbare Netto-Realisierung als Grundlage der 3 % prüfen."]
].map(([n,t,d])=><article className="step-card" key={n}><span className="step-num">{n}</span><h3>{t}</h3><p>{d}</p></article>)}</div>
<p className="note">Das Erfolgsmodell befindet sich in der vertraglichen/rechtlichen Ausarbeitung. Es sind noch keine Kundenrechnung und kein Recovery-Ledger implementiert.</p>
</section><ConversionCTA/></>}
