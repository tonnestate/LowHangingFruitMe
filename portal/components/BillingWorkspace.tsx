"use client";
import {useState} from "react";

type BillingPacket={
 packet_id:string;state:"PREPARED"|"RELEASED"|"VOIDED";
 net_realization:string;fee_net:string;fee_rate_bps:number;
 fee_due_net:string;invoice_created:boolean;stale:boolean;
 requires_external_correction:boolean;external_invoice_required:boolean;
 prepared_by:string;released_by:string|null;external_correction_ref:string|null;
 events:Array<{event_type:string;actor:string;reason:string|null;recorded_at:string}>;
};
type Props={tenantId:string;legalEntityId:string;initialAuditId:string};
const UUID=/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/;

function validId(value:string):string{
 const id=value.trim().toLowerCase();
 if(!UUID.test(id))throw new Error("GUELTIGE_UUID_ERFORDERLICH");
 return id;
}
function messageFrom(value:unknown,status:number):string{
 const detail=value&&typeof value==="object"&&"detail" in value
  ?(value as {detail:unknown}).detail:value;
 if(detail&&typeof detail==="object"&&"code" in detail){
  const code=(detail as {code:unknown}).code;
  if(typeof code==="string")return code;
 }
 return "HTTP_"+status;
}

export function BillingWorkspace({tenantId,legalEntityId,initialAuditId}:Props){
 const [auditId,setAuditId]=useState(initialAuditId);
 const [packetId,setPacketId]=useState("");
 const [packet,setPacket]=useState<BillingPacket|null>(null);
 const [reviewedTerms,setReviewedTerms]=useState(false);
 const [reason,setReason]=useState("");
 const [correctionRef,setCorrectionRef]=useState("");
 const [busy,setBusy]=useState(false);
 const [notice,setNotice]=useState("");

 const scope={tenant_id:tenantId,legal_entity_id:legalEntityId};
 const query=new URLSearchParams(scope).toString();
 const validScope=Boolean(tenantId&&legalEntityId);
 async function request<T>(path:string,body?:Record<string,unknown>):Promise<T>{
  if(!validScope)throw new Error("MANDANT_UND_GESELLSCHAFT_ERFORDERLICH");
  const response=await fetch("/api/finance/"+path,{
   method:body?"POST":"GET",cache:"no-store",
   ...(body?{headers:{"Content-Type":"application/json"},body:JSON.stringify({...scope,...body})}:{})
  });
  const payload:unknown=await response.json().catch(()=>null);
  if(!response.ok)throw new Error(messageFrom(payload,response.status));
  if(!payload||typeof payload!=="object")throw new Error("UNGUELTIGE_API_ANTWORT");
  return payload as T;
 }
 async function run(task:()=>Promise<string>){
  setBusy(true);setNotice("");
  try{setNotice(await task());}
  catch(error){
   setNotice("Vorgang abgelehnt: "+(error instanceof Error?error.message:"UNKNOWN"));
  }finally{setBusy(false);}
 }
 function prepare(){
  void run(async()=>{
   const id=validId(auditId);
   const response=await request<{packet_id:string;status:string;invoice_created:boolean}>(
    "audits/"+id+"/billing-packets",{});
   setPacketId(response.packet_id);
   setPacket(null);setReviewedTerms(false);
   return "Honorarakte "+response.packet_id+" ist "+response.status+
    ". Freigabe erfordert einen zweiten berechtigten Bearbeiter; keine Rechnung erzeugt.";
  });
 }
 function read(){
  void run(async()=>{
   const id=validId(packetId);
   const result=await request<BillingPacket>("billing-packets/"+id+"?"+query);
   setPacket(result);
   setReviewedTerms(false);
   return result.stale
    ?"Honorarakte ist veraltet. Keine Freigabe auf dieser Grundlage."
    :"Honorarakte gelesen: "+result.state+". Keine Rechnung automatisch erstellt.";
  });
 }
 function release(){
  void run(async()=>{
   const id=validId(packetId);
   if(!reviewedTerms)throw new Error("VERTRAGSBEDINGUNGEN_NICHT_BESTAETIGT");
   if(packet?.stale)throw new Error("VERALTETE_HONORARAKTE");
   const response=await request<{status:string;invoice_created:boolean}>(
    "billing-packets/"+id+"/release",{confirm_commercial_terms_review:true});
   setPacket(null);setReviewedTerms(false);
   return "Interne Honorarübergabe "+response.status+
    ". Externe Rechnungserstellung und gesonderter Rechnungsnachweis erforderlich.";
  });
 }
 function voidPacket(){
  void run(async()=>{
   const id=validId(packetId);
   if(!reason.trim()||!correctionRef.trim())
    throw new Error("KORREKTURBEGRUENDUNG_UND_EXTERNER_BELEG_ERFORDERLICH");
   const response=await request<{status:string;invoice_created:boolean}>(
    "billing-packets/"+id+"/void",{
     reason:reason.trim(),external_correction_ref:correctionRef.trim(),
    });
   setPacket(null);setReviewedTerms(false);
   return "Interne Honorarübergabe "+response.status+
    ". Externe Rechnung beziehungsweise Gutschrift getrennt berichtigen.";
  });
 }

 return <fieldset disabled={busy||!validScope}>
  <legend>7 · Kaufmännische Honorarübergabe</legend>
  <p className="note">Nur nach unabhängiger Realisierungsprüfung und extern
   bestätigter Kunden-/Honorarvereinbarung. Das Berechnen einer Differenz und
   eine Finanzbestätigung allein lösen keine Rechnung aus. Vorbereitung,
   Freigabe und Widerruf unterliegen getrennten serverseitigen Billing-Rollen.</p>
  {notice&&<p role="status" className="workspace-notice">{notice}</p>}
  <div className="workspace-grid">
   <label>Audit-ID
    <input value={auditId} onChange={e=>{setAuditId(e.target.value);setPacketId("");
      setPacket(null);setReviewedTerms(false);}}/>
   </label>
  </div>
  <button className="button-secondary" type="button" onClick={prepare}>
   Honorarakte aus bestätigter Realisierung vorbereiten
  </button>
  <div className="workspace-grid">
   <label>Honorarakten-ID
    <input value={packetId} onChange={e=>{setPacketId(e.target.value);
      setPacket(null);setReviewedTerms(false);}}/>
   </label>
  </div>
  <button className="button-secondary" type="button" onClick={read}>
   Honorarakte mit Billing-Leserecht prüfen
  </button>
  {packet&&<div className="info-block">
   <p>Status: <strong>{packet.state}</strong>{packet.stale?" – VERALTET":""}</p>
   <p>Bestätigte Nettorealisierung: {packet.net_realization} EUR.
    Honorar ({(packet.fee_rate_bps/100).toLocaleString("de-DE")} %):
    <strong> {packet.fee_net} EUR.</strong></p>
   <p>Bereits fällig laut Anwendung: {packet.fee_due_net} EUR.
    Rechnung erstellt: {packet.invoice_created?"Ja":"Nein"}.</p>
   <p>Vorbereitet von: {packet.prepared_by}.
    Freigegeben von: {packet.released_by||"noch niemand"}.</p>
   {packet.requires_external_correction&&
    <p className="note">Der freigegebene Belegstand hat sich verändert.
     Externe Rechnungskorrektur ist gesondert nachzuweisen.</p>}
   {packet.external_invoice_required&&<p className="note">Die interne Freigabe
    ist keine Rechnung; ein externer Rechnungsprozess ist erforderlich.</p>}
   {packet.external_correction_ref&&
    <p>Externer Korrekturbeleg: {packet.external_correction_ref}</p>}
   {packet.events.map((event,i)=><p key={event.event_type+"-"+i}>
    {event.event_type} · {event.actor} · {event.recorded_at}
    {event.reason?" · "+event.reason:""}
   </p>)}
  </div>}
  <label><input type="checkbox" checked={reviewedTerms}
   onChange={e=>setReviewedTerms(e.target.checked)}/>
   Ich habe die extern dokumentierten Vertrags-/Honorarbedingungen und den
   aktuellen Belegstand persönlich geprüft.</label>
  <button className="button-secondary" type="button" disabled={!reviewedTerms||packet?.stale===true}
   onClick={release}>Honorarakte durch zweiten Billing-Bearbeiter freigeben</button>
  <p className="note">Nur ein anderer, separat berechtigter Billing-Bearbeiter
   kann eine PREPARED-Akte freigeben. Die API prüft den Status unter
   Transaktionssperre erneut.</p>
  <div className="workspace-grid">
   <label>Korrekturbegründung
    <input value={reason} maxLength={200} onChange={e=>setReason(e.target.value)}/>
   </label>
   <label>Referenz auf externe Rechnungs-/Gutschriftkorrektur
    <input value={correctionRef} maxLength={200}
     onChange={e=>setCorrectionRef(e.target.value)}/>
   </label>
  </div>
  <button className="button-secondary" type="button" onClick={voidPacket}>
   Freigegebene Honorarakte mit Korrekturbeleg widerrufen
  </button>
  <p className="note">Nach Änderungen am Recovery-Ledger bitte die Honorarakte
   erneut abrufen. PREPARED, RELEASED und VOIDED erzeugen weder
   automatisch eine Rechnung noch einen Zahlungseingang.</p>
 </fieldset>;
}
