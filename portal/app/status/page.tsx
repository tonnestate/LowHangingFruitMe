import type {Metadata} from "next";
import Link from "next/link";
import {PageIntro} from "../../components/PageIntro";
export const metadata:Metadata={title:"Produktstatus und technische Grenzen",description:"Was LowHangingFruitMe tatsächlich implementiert hat – und welche Onlinefunktionen noch fehlen."};
const rows=[
 ["Deterministische Bonusberechnung","Python-Kern implementiert und synthetisch getestet"],
 ["CSV-/XLSX-Import","Lokale Parser, Vorschlagsmapping und Freigabe implementiert"],
 ["Vertragsdokumente","PDF-Adapter vorhanden; reale OCR-Abnahme ausstehend"],
 ["Freigaben","Signatur- und MariaDB-Regelregister implementiert"],
 ["Öffentlicher Kunden-Upload","Noch nicht verfügbar"],
 ["Selbstbedienungsportal und REST-API","Noch nicht verfügbar"],
 ["Lexware-, Odoo- und andere ERP-Connectoren","Noch nicht verfügbar"],
 ["Realisiertes Recovery und Gebührenabrechnung","Noch nicht implementiert"],
 ["SOC-2-Type-II-Prüfung","Nicht vorhanden"]
];
export default function Status(){return <><PageIntro eyebrow="Transparenter Entwicklungsstand" title="Was bereits funktioniert – und was noch nicht." description="Die öffentliche Website ist keine Behauptung, dass alle beschriebenen CFO-Leistungen oder eine vollständig betreibbare SaaS-Plattform vorhanden sind."/>
<section className="content-page"><h2>Implementierungsübersicht</h2><div className="feature-grid" style={{gridTemplateColumns:"1fr"}}>{rows.map(([title,state])=><div className="feature-card" key={title}><h3>{title}</h3><p>{state}</p></div>)}</div>
<h2>Nachweise</h2><p>Der aktuelle Entwicklungsstand ist im <Link href="https://github.com/tonnestate/LowHangingFruitMe/blob/main/docs/IMPLEMENTATION_STATUS.md">GitHub-Statusdokument</Link> beschrieben. Eine vollständige Live-Kundenprüfung ist damit nicht nachgewiesen.</p></section></>}
