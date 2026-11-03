import type {Metadata} from "next";
export const metadata:Metadata={title:"Impressum",robots:{index:false,follow:false}};
export default function Imprint(){
 const ready=process.env.PUBLIC_LAUNCH_APPROVED==="true";
 return <section className="content-page"><h1>Impressum</h1>{ready?
 <><p>Betreiber: {process.env.SITE_OPERATOR_NAME}</p><p style={{whiteSpace:"pre-line"}}>{process.env.SITE_OPERATOR_ADDRESS}</p><p>E-Mail: {process.env.SITE_OPERATOR_EMAIL}</p>
 <p>Diese Angaben ersetzen nicht die juristische Prüfung der gesetzlichen Impressumspflichten und etwaiger weiterer Pflichtangaben.</p></>:
 <><h2>Staging – Betreiberangaben ausstehend</h2><p>Die rechtlich erforderlichen Betreiber- und Kontaktangaben sind noch nicht freigegeben. Diese Website darf in diesem Zustand nicht öffentlich vermarktet werden.</p></>}</section>;
}
