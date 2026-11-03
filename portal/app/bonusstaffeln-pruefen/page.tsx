import type {Metadata} from "next";
import Link from "next/link";
import {PageIntro} from "../../components/PageIntro";
import {ConversionCTA} from "../../components/ConversionCTA";
export const metadata:Metadata={title:"Bonusstaffeln prüfen und korrekt berechnen",description:"Rückwirkende Staffelboni, marginale Stufen und feste Schwellenprämien fachlich unterscheiden."};
export default function Tiers(){return <><PageIntro eyebrow="Fachthema Lieferantenboni" title="Bonusstaffeln sind nicht alle gleich." description="Ob eine erreichte Umsatzstufe für den gesamten Jahresumsatz oder nur für zusätzliche Umsatzteile gilt, verändert den berechneten Bonus. Entscheidend ist der Wortlaut der Vereinbarung."/>
<section className="content-page"><h2>Rückwirkende Staffel</h2><p>Bei einer rückwirkenden Staffel kann die erreichte Prozentstufe auf die gesamte vertraglich bonusfähige Basis angewendet werden. Das muss ausdrücklich aus der Vertragsregel hervorgehen.</p>
<h2>Marginale Staffel</h2><p>Bei einer marginalen Staffel können für verschiedene Umsatzscheiben unterschiedliche Sätze gelten. Eine reine Betrachtung der höchsten erreichten Stufe wäre dann falsch.</p>
<h2>Feste Schwellenprämie</h2><p>Manche Bonusprogramme gewähren ab einer erreichten Schwelle einen festen Betrag. Auch das ist von einer prozentualen Vergütung abzugrenzen.</p>
<h2>Was das System bereits kann</h2><p>Diese drei Modelle werden im vorhandenen Python-Rechenkern mit Dezimalarithmetik unterstützt. Der öffentliche Upload und ein selbstständig nutzbares Kundenportal sind noch nicht freigegeben.</p>
<p><Link href="/bonusgutschriften-abgleichen">Weiter: Gutschriften korrekt zuordnen</Link></p></section><ConversionCTA/></>}
