import type {Metadata} from "next";
import {PageIntro} from "../../components/PageIntro";
export const metadata:Metadata={title:"Eignungscheck für Lieferantenboni",description:"Prüfen, ob Ihre Lieferantenvereinbarungen und ERP-Exporte für einen Pilot-Audit geeignet sind. Noch kein öffentlicher Finanzdaten-Upload."};
const checks=[
"Schriftliche Lieferantenbonus-Vereinbarung mit einem klaren Abrechnungszeitraum",
"Elektronischer Einkaufsdatenexport aus dem ERP (CSV oder Excel)",
"Abrechnungen/Gutschriften des betreffenden Lieferanten",
"Ein fachlich verantwortlicher Ansprechpartner aus Finanzen oder Einkauf"
];
export default function Check(){
 const email=process.env.CONTACT_EMAIL;
 const subject=encodeURIComponent("LowHangingFruitMe – Anfrage zum Eignungscheck");
 const body=encodeURIComponent("Unternehmen:\nAnsprechpartner:\nBranche:\nAnzahl relevanter Lieferantenvereinbarungen:\nERP-System:\n\nBitte keine vertraulichen Verträge, Rechnungen oder Kundendaten per ungesicherter E-Mail mitsenden.");
 return <><PageIntro eyebrow="Eignungscheck · Pilotvorbereitung" title="Lohnt sich eine beleggestützte Bonusprüfung?" description="Die erste Frage lautet nicht, welches ERP Sie einsetzen. Entscheidend ist, ob Bonusregeln und die zugehörigen Einkaufs- und Gutschriftendaten ausreichend nachvollziehbar sind."/>
 <section className="content-page"><h2>Vier Voraussetzungen</h2><ul className="bullet-list">{checks.map(c=><li key={c}>{c}</li>)}</ul>
 <div className="info-block"><h3>Keine Finanzunterlagen öffentlich hochladen</h3><p>Ein geschützter Kunden-Upload ist noch nicht freigeschaltet. Bitte über diese Seite keine Verträge, Buchungsdaten oder personenbezogenen Finanzunterlagen übermitteln.</p></div>
 <h2>Anfrage zur Pilotphase</h2>
 {email?<><p>Für eine unverbindliche erste Eignungsabklärung kann eine kurze Anfrage ohne vertrauliche Anhänge gesendet werden.</p><a className="button-primary" href={"mailto:"+email+"?subject="+subject+"&body="+body}>Eignungscheck per E-Mail anfragen</a></>:
 <div className="info-block"><h3>Annahme noch nicht aktiviert</h3><p>Der öffentliche Kontaktkanal wird erst nach Betreiber-, Datenschutz- und Sicherheitsfreigabe eingerichtet. Auf dieser Staging-Seite wird keine Anfrage erfasst.</p></div>}
 <p className="note">Die 3 % Erfolgsprovision sind ein vorgesehenes Vertragsmodell. Eine Eignungsanfrage ist weder ein rechtsverbindlicher Auftrag noch eine Zustimmung zu Kosten.</p>
 </section></>;
}
