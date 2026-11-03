import type {Metadata} from "next";
import {auth, oidcConfigured, signIn, signOut} from "../../auth";
import {WorkspaceClient} from "../../components/WorkspaceClient";

export const dynamic="force-dynamic";
export const metadata:Metadata={
  title:"Geschützter Arbeitsplatz",robots:{index:false,follow:false}
};
export default async function Page(){
 if(!oidcConfigured||!process.env.LHFM_API_INTERNAL_URL){
  return <section className="content-page">
   <span className="eyebrow">Geschützter Finanzarbeitsplatz</span>
   <h1>Unternehmenszugang noch nicht aktiviert.</h1>
   <p>Identitätsanbieter und private API müssen zuerst eingerichtet werden.
   Bis dahin nimmt die Website keine Finanzdaten entgegen.</p>
  </section>;
 }
 const session=await auth();
 if(!session?.user?.email&&!session?.user?.name){
  return <section className="content-page"><span className="eyebrow">Geschützter Zugang</span>
   <h1>Mit Unternehmenskonto anmelden</h1>
   <form action={async()=>{"use server";await signIn("lhfm-oidc",{redirectTo:"/arbeitsplatz"});}}>
    <button className="button-primary" type="submit">Sicher anmelden</button>
   </form>
  </section>;
 }
 return <section className="section workspace">
  <div className="section-heading"><span className="eyebrow">Pilot · Financial Recovery</span>
   <h1>Finanzprüfung</h1><p>ERP-Exporte und Vertrag einlesen, die Zuordnungen fachlich
    prüfen, Berechnung freigeben und realisierte Beträge nachvollziehbar verfolgen.</p>
  </div>
  <form action={async()=>{"use server";await signOut({redirectTo:"/"});}}>
   <button className="button-secondary" type="submit">Abmelden</button>
  </form>
  <WorkspaceClient/>
 </section>;
}
