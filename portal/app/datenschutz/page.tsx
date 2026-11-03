import type {Metadata} from "next";
export const metadata:Metadata={title:"Datenschutz",robots:{index:false,follow:false}};
export default function Privacy(){
 const approved=process.env.PUBLIC_LAUNCH_APPROVED==="true";
 const notice=process.env.SITE_PRIVACY_NOTICE;
 return <section className="content-page"><h1>Datenschutzhinweise</h1>
 {approved&&notice?<div style={{whiteSpace:"pre-line"}}>{notice}</div>:<>
 <h2>Vorläufiger Entwicklungsstand</h2><p>Diese Seite enthält noch keine vollständige, rechtlich freigegebene Datenschutzerklärung für den späteren öffentlichen Betrieb. Die Website ist bis dahin für Suchmaschinen gesperrt.</p>
 <h2>Technische Konzeption</h2><p>Die Staging-Website verwendet keine analytischen Tracking-Cookies und nimmt keine Vertrags- oder Finanzdaten entgegen. Technische Serverzugriffsprotokolle und die tatsächlichen Hosting- und Dienstleisterinformationen müssen vor dem öffentlichen Betrieb dokumentiert werden.</p>
 <h2>Erforderliche Freigabe</h2><p>Vor dem Livebetrieb müssen Verantwortlicher, Kontakt- und Betroffenenrechte, Zwecke und Rechtsgrundlagen, Speicherdauer, Hosting- und Auftragsverarbeitungsinformationen sowie mögliche Cookies und Dienste vollständig und zutreffend angegeben werden.</p>
 </>}
 </section>;
}
