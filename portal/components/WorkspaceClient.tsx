"use client";
import {useState} from "react";

type Dataset="transactions"|"settlements";
type ContractSegment={evidence_ref:string;text:string;pages:number[]};
type Preview={headers:string[];rows:number;source_sha256:string;
  proposed_mapping:Record<string,string[]>;options:Record<string,string>};
type Uploaded={upload_id:string;kind:string;sha256:string;state:string};
type Audit={audit_id:string;status:string;audit_executed:boolean};
type Ledger={confirmed_realization_net:string;fee_proposal_net:string;fee_rate:string;
  fee_due_net:string;events:Array<{event_id:string;state:string;amount_net:string;kind:string}>};
const TX=["external_id","supplier_id","date","currency","amount_net","kind","posted","basis"];
const ST=["external_id","supplier_id","date","currency","amount_net","kind",
  "posted","agreement_id","period_start","period_end"];
const LABEL:Record<string,string>={external_id:"Belegnummer",supplier_id:"Kreditor",
 date:"Buchungsdatum",currency:"Währung",amount_net:"Nettobetrag",
 kind:"Vorgangsart",posted:"Gebucht",basis:"Bonusbasis",
 agreement_id:"Vertragsnummer",period_start:"Bonusbeginn",period_end:"Bonusende"};

async function call<T>(path:string,init:RequestInit={}):Promise<T>{
 const result=await fetch("/api/finance/"+path,{cache:"no-store",...init});
 const value:unknown=await result.json().catch(()=>({code:"INVALID_RESPONSE"}));
 if(!result.ok){
  const detail=value && typeof value==="object" && "detail" in value?
   (value as {detail:unknown}).detail:value;
  const code=detail && typeof detail==="object" && "code" in detail?
   String((detail as {code:unknown}).code):"HTTP_"+result.status;
  throw new Error(code);
 }
 return value as T;
}
function jsonBody(value:unknown):RequestInit{
 return {method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(value)};
}
async function sha256File(buffer:ArrayBuffer){
 const digest=await crypto.subtle.digest("SHA-256",buffer);
 return Array.from(new Uint8Array(digest),b=>b.toString(16).padStart(2,"0")).join("");
}
function plan(dataset:Dataset,preview:Preview,choices:Record<string,string>,
 locale:{decimal:string;date:string;boolean:string},actor:string){
 const mapping:Record<string,string>={},constants:Record<string,string>={};
 for(const name of dataset==="transactions"?TX:ST){
  const item=choices[name];
  if(!item)throw new Error("SPALTE_NICHT_BESTAETIGT_"+name);
  if(item.startsWith("col:"))mapping[name]=item.substring(4);
  else if(item.startsWith("const:"))constants[name]=item.substring(6);
  else throw new Error("SPALTENFEHLER");
 }
 if(!locale.decimal||!locale.date||!locale.boolean)throw new Error("DATENFORMAT_NICHT_BESTAETIGT");
 return {source_sha256:preview.source_sha256,dataset,mapping,constants,
  sheet_name:preview.options.sheet||null,decimal_format:locale.decimal,
  date_format:locale.date,boolean_format:locale.boolean,
  reviewed_by:actor,confirmed:true};
}
function MapFields({dataset,preview,value,change}:{dataset:Dataset;preview:Preview;
 value:Record<string,string>;change:(v:Record<string,string>)=>void}){
 return <div className="map-fields">{(dataset==="transactions"?TX:ST).map(field=>
  <label key={field}>{LABEL[field]||field}<select value={value[field]||""}
   onChange={e=>change({...value,[field]:e.target.value})}>
   <option value="">Quelle ausdrücklich auswählen</option>
   {preview.headers.map(head=><option value={"col:"+head} key={head}>{head}</option>)}
   {(field==="currency"?["EUR"]:field==="basis"?["INVOICE"]:
     field==="kind"?(dataset==="transactions"?["PURCHASE","RETURN"]:["CREDIT"]):[]
   ).map(v=><option value={"const:"+v} key={v}>Bestätigte Konstante: {v}</option>)}
  </select></label>
 )}</div>;
}
export function WorkspaceClient(){
 const [tenant,setTenant]=useState(""),[entity,setEntity]=useState("");
 const [actor,setActor]=useState("");
 const [files,setFiles]=useState<Record<string,File|null>>({
  transactions:null,settlements:null,contract:null,recovery:null});
 const [sources,setSources]=useState<Record<string,Uploaded>>({});
 const [candidateId,setCandidateId]=useState("");
 const [segments,setSegments]=useState<ContractSegment[]>([]);
 const [previews,setPreviews]=useState<Partial<Record<Dataset,Preview>>>({});
 const [maps,setMaps]=useState<Record<Dataset,Record<string,string>>>({
  transactions:{},settlements:{}});
 const [sheet,setSheet]=useState("");
 const [locale,setLocale]=useState({decimal:"",date:"",boolean:""});
 const [sourceSystem,setSourceSystem]=useState("");
 const [rule,setRule]=useState({rule_id:"",revision:"1",supplier_id:"",
  agreement_id:"",period_start:"",period_end:"",rate:"",evidence:"",source_revision:""});
 const [control,setControl]=useState({tx_count:"",tx_total:"",tx_ref:"",
  st_count:"",st_total:"",st_ref:""});
 const [review,setReview]=useState({contract:false,mapping:false,tx:false,st:false,agreements:false});
 const [bundle,setBundle]=useState("");
 const [audit,setAudit]=useState<Audit|null>(null);
 const [report,setReport]=useState<Record<string,unknown>|null>(null);
 const [ledger,setLedger]=useState<Ledger|null>(null);
 const [recoveryAmount,setRecoveryAmount]=useState("");
 const [recoveryKind,setRecoveryKind]=useState<"REALIZATION"|"REVERSAL">("REALIZATION");
 const [reversalId,setReversalId]=useState("");
 const [financeEvent,setFinanceEvent]=useState("");
 const [caseDirective,setCaseDirective]=useState<"DISPUTED"|"CLOSED"|"OPEN">("DISPUTED");
 const [caseReason,setCaseReason]=useState("");
 const [financeDecision,setFinanceDecision]=useState<"CONFIRM"|"REJECT">("CONFIRM");
 const [busy,setBusy]=useState(false),[message,setMessage]=useState("");
 const scope={tenant_id:tenant.trim(),legal_entity_id:entity.trim()};
 const qs=new URLSearchParams(scope).toString();
 const run=async(task:()=>Promise<string>)=>{
  setBusy(true);setMessage("");
  try{setMessage(await task());}
  catch(e){setMessage("Vorgang abgelehnt: "+(e instanceof Error?e.message:"UNKNOWN"));}
  finally{setBusy(false);}
 };
 async function upload(file:File,kind:string):Promise<Uploaded>{
  if(file.size<1||file.size>16*1024*1024)throw new Error("DATEIGROESSE_UNGUELTIG");
  const bytes=await file.arrayBuffer();
  const digest=await sha256File(bytes);
  const intent=await call<{upload_id:string}>("uploads",jsonBody({
   ...scope,kind,byte_size:bytes.byteLength,sha256:digest,
  }));
  const response=await call<Uploaded>("uploads/"+intent.upload_id+"/content?"+qs,{
   method:"PUT",headers:{"Content-Type":"application/octet-stream"},
   body:new Blob([bytes],{type:"application/octet-stream"}),
  });
  if(response.state!=="CLEAN")throw new Error("DATEI_NICHT_GESCANNT");
  return {...response,kind};
 }
 const authorize=()=>run(async()=>{
  if(!scope.tenant_id||!scope.legal_entity_id)throw new Error("MANDANT_FEHLT");
  const r=await call<{subject:string}>("me?"+qs);
  setActor(r.subject);return "Verifizierter Prüfer: "+r.subject;
 });
 const ingest=()=>run(async()=>{
  if(!actor)throw new Error("BERECHTIGUNG_ERFORDERLICH");
  const tx=files.transactions,st=files.settlements,co=files.contract;
  if(!tx||!st||!co)throw new Error("DREI_QUELLDATEIEN_ERFORDERLICH");
  const a=await upload(tx,tx.name.toLowerCase().endsWith(".xlsx")?"ERP_XLSX":"ERP_CSV");
  const b=await upload(st,st.name.toLowerCase().endsWith(".xlsx")?"ERP_XLSX":"ERP_CSV");
  if(!co.name.toLowerCase().endsWith(".pdf"))throw new Error("VERTRAG_NUR_PDF");
  const c=await upload(co,"CONTRACT_PDF");
  setSources({transactions:a,settlements:b,contract:c});
  setBundle("");setAudit(null);setLedger(null);setPreviews({});
  setCandidateId("");setSegments([]);setRule(v=>({...v,evidence:""}));
  return "Die drei Quelldateien sind geprüft und gespeichert. Fachfreigabe steht aus.";
 });
 const inspect=()=>run(async()=>{
  const next:Partial<Record<Dataset,Preview>>={};
  for(const type of ["transactions","settlements"] as Dataset[]){
   const up=sources[type];
   if(!up)throw new Error("DATEI_FEHLT");
   const query=qs+"&dataset="+type+(sheet?"&sheet_name="+encodeURIComponent(sheet):"");
   const p=await call<Preview>("uploads/"+up.upload_id+"/inspect?"+query);
   next[type]=p;
   const suggested:Record<string,string>={};
   for(const [key,candidates] of Object.entries(p.proposed_mapping)){
    if(candidates.length===1)suggested[key]="col:"+candidates[0];
   }
   setMaps(old=>({...old,[type]:suggested}));
  }
  setPreviews(next);
  return "Spaltenvorschläge erstellt. Bitte alle Zuordnungen prüfen.";
 });
 const extractContract=()=>run(async()=>{
  if(!actor||!sources.contract)throw new Error("VERTRAGSUPLOAD_ERFORDERLICH");
  if(!rule.agreement_id||!rule.rule_id||!rule.revision||!rule.source_revision)
   throw new Error("VERTRAGSIDENTITAET_ERFORDERLICH");
  const result=await call<{candidate_id:string;segments:ContractSegment[];state:string}>(
   "contract-candidates",jsonBody({
     ...scope,contract_upload_id:sources.contract.upload_id,
     agreement_id:rule.agreement_id,rule_id:rule.rule_id,
     rule_revision:rule.revision,source_revision_id:rule.source_revision,
   }));
  setCandidateId(result.candidate_id);setSegments(result.segments);
  setRule(v=>({...v,evidence:""}));
  return "Vertragsfundstellen extrahiert. Bitte Dokument und konkrete Klausel manuell vergleichen.";
 });
 const approve=()=>run(async()=>{
  if(!candidateId)throw new Error("DOKUMENTENGEBUNDENER_KANDIDAT_FEHLT");
  if(!actor||!previews.transactions||!previews.settlements)
   throw new Error("DATENPRUEFUNG_FEHLT");
  if(Object.values(review).some(v=>!v))throw new Error("FACHLICHE_BESTAETIGUNG_FEHLT");
  if(!sourceSystem||Object.values(rule).some(v=>!v)||Object.values(control).some(v=>!v))
   throw new Error("VERTRAGSREGEL_ODER_ERP_KONTROLLREPORT_UNVOLLSTAENDIG");
  const payload={
   ...scope,transactions_upload_id:sources.transactions.upload_id,
   settlements_upload_id:sources.settlements.upload_id,
   contract_upload_id:sources.contract.upload_id,
   source_system:sourceSystem,source_revision_id:rule.source_revision,
   rule:{rule_id:rule.rule_id,revision:rule.revision,kind:"FLAT_RATE",
    supplier_id:rule.supplier_id,agreement_id:rule.agreement_id,
    currency:"EUR",basis:"INVOICE",period_start:rule.period_start,
    period_end:rule.period_end,rate:rule.rate,approved:true,evidence_refs:[rule.evidence]},
   transaction_plan:plan("transactions",previews.transactions,maps.transactions,locale,actor),
   settlement_plan:plan("settlements",previews.settlements,maps.settlements,locale,actor),
   controls:{source_system:sourceSystem,supplier_id:rule.supplier_id,
    agreement_id:rule.agreement_id,period_start:rule.period_start,
    period_end:rule.period_end,transactions:{row_count:Number(control.tx_count),
     net_total:control.tx_total,source_reference:control.tx_ref},
    settlements:{row_count:Number(control.st_count),net_total:control.st_total,
     source_reference:control.st_ref}},
   completeness:{transactions_complete:true,settlements_complete:true,agreements_complete:true},
   confirm_contract_review:true,confirm_mapping_review:true,
  };
  await call("contract-candidates/"+candidateId+"/review",jsonBody({
   ...scope,rule:payload.rule,confirm_clause_review:true,
  }));
  const response=await call<{bundle_id:string}>("bundles",jsonBody({
   ...payload,candidate_id:candidateId,
  }));
  setBundle(response.bundle_id);setAudit(null);setLedger(null);
  return "Quellen und Vertragsregel signiert registriert: "+response.bundle_id;
 });
 const calculate=()=>run(async()=>{
  const result=await call<Audit>("audits",{
   ...jsonBody({...scope,bundle_id:bundle}),
   headers:{"Content-Type":"application/json","Idempotency-Key":crypto.randomUUID()},
  });
  setAudit(result);
  const detail=await call<{report:Record<string,unknown>}>("audits/"+result.audit_id+"?"+qs);
  setReport(detail.report);
  return result.audit_executed?"Audit durchgeführt – noch keine wirtschaftliche Realisierung.":
   "Audit erfordert weitere Daten oder Freigaben.";
 });
 const downloadReport=(fmt:"pdf"|"xlsx"|"json")=>run(async()=>{
  if(!audit||audit.status!=="COMPLETED")throw new Error("FREIGEGEBENER_AUDIT_FEHLT");
  const response=await fetch("/api/finance/audits/"+audit.audit_id+
   "/report."+fmt+"?"+qs,{cache:"no-store"});
  if(!response.ok)throw new Error("BERICHT_NICHT_VERFUEGBAR_"+response.status);
  const blob=await response.blob();
  const url=URL.createObjectURL(blob);
  try{
   const link=document.createElement("a");
   link.href=url;link.download="lhfm-"+audit.audit_id+"."+fmt;
   document.body.appendChild(link);link.click();link.remove();
  }finally{URL.revokeObjectURL(url);}
  return "Geprüfter Bericht als "+fmt.toUpperCase()+" bereitgestellt.";
 });
 const readLedger=()=>run(async()=>{
  if(!audit)throw new Error("AUDIT_FEHLT");
  setLedger(await call<Ledger>("audits/"+audit.audit_id+"/fee-ledger?"+qs));
  return "Recovery-Ledger aktualisiert.";
 });
 const reportRealization=()=>run(async()=>{
  if(!audit||!files.recovery||!recoveryAmount)throw new Error("NACHWEIS_FEHLT");
  const evidence=await upload(files.recovery,"RECOVERY_PDF");
  const result=await call<{event_id:string}>("audits/"+audit.audit_id+"/recovery-events",{
   ...jsonBody({...scope,kind:recoveryKind,amount_net:recoveryAmount,
    evidence_upload_id:evidence.upload_id,
    reverses_event_id:recoveryKind==="REVERSAL"?reversalId:null}),
   headers:{"Content-Type":"application/json","Idempotency-Key":crypto.randomUUID()},
  });
  setFinanceEvent(result.event_id);
  return "Zur getrennten Prüfung gemeldet: "+result.event_id;
 });
 const markCaseStatus=()=>run(async()=>{
  if(!audit||!caseReason.trim())throw new Error("FALLSTATUS_UND_BEGRUENDUNG_ERFORDERLICH");
  const result=await call<{directive:string}>(
   "audits/"+audit.audit_id+"/case-status",
   jsonBody({...scope,directive:caseDirective,reason:caseReason.trim()})
  );
  return "Finanzstatus dokumentiert: "+result.directive;
 });
 const financeReview=()=>run(async()=>{
  if(!financeEvent)throw new Error("EREIGNIS_ID_FEHLT");
  const result=await call<{status:string}>("recovery-events/"+financeEvent+"/review",
   jsonBody({...scope,decision:financeDecision,confirm_evidence_review:true}));
  return "Finanzentscheidung: "+result.status+". Keine Rechnung erstellt.";
 });

 const readiness=report?.readiness && typeof report.readiness==="object"
  ? report.readiness as {status?:string;
     issues?:Array<{code:string;field:string;explanation:string;severity:string}>;
     quality_metrics?:{data_coverage_pct:string|null;rule_clarity_pct:string|null;
       reconciliation_completeness_pct:string|null;source_ledger_completeness_proven:boolean}}
  : null;
 const quality=readiness?.quality_metrics;
 return <div className="workspace-content">
  <p className="note">Finanzdaten bleiben im geschützten Pilotprozess. Das Sprachmodell
  erteilt keine Vertragsfreigabe. Jede Buchung muss auf prüfbare Quellen zurückgehen.</p>
  {message&&<p role="status" className="workspace-notice">{message}</p>}
  <fieldset disabled={busy}><legend>1 · Unternehmen und Berechtigung</legend>
   <div className="workspace-grid">
    <label>Mandant-ID<input value={tenant} onChange={e=>{setTenant(e.target.value);setActor("");}}/></label>
    <label>Gesellschafts-ID<input value={entity} onChange={e=>{setEntity(e.target.value);setActor("");}}/></label>
   </div>
   <button className="button-secondary" type="button" onClick={authorize}>Berechtigung prüfen</button>
   {actor&&<p>Angemeldet als berechtigter Reviewer: {actor}</p>}
  </fieldset>
  <fieldset disabled={busy||!actor}><legend>2 · Daten und Vertragsdokument</legend>
   <div className="workspace-grid">
    {([["transactions","Einkaufsbuchungen · CSV/XLSX",".csv,.xlsx"],
       ["settlements","Gutschriften · CSV/XLSX",".csv,.xlsx"],
       ["contract","Vereinbarung · PDF",".pdf"]] as const).map(([role,label,accept])=>
     <label key={role}>{label}<input type="file" accept={accept}
       onChange={e=>setFiles(v=>({...v,[role]:e.target.files?.[0]??null}))}/></label>)}
   </div>
   <button className="button-primary" type="button" onClick={ingest}>Drei Dateien gesichert hochladen</button>
   {sources.contract&&<p>Upload abgeschlossen; fachliche Regel- und Datenprüfung noch offen.</p>}
  </fieldset>
  <fieldset disabled={busy||!sources.contract}><legend>3 · Spalten und Datenformat prüfen</legend>
   <label>Optionales Excel-Tabellenblatt<input value={sheet} onChange={e=>setSheet(e.target.value)}/></label>
   <button className="button-secondary" type="button" onClick={inspect}>Spalten erkennen</button>
   {(["transactions","settlements"] as Dataset[]).map(type=>previews[type]&&
    <div className="map-section" key={type}>
     <h3>{type==="transactions"?"Einkauf":"Gutschriften"} – {previews[type]!.rows} Zeilen</h3>
     <MapFields dataset={type} preview={previews[type]!} value={maps[type]}
      change={v=>setMaps(old=>({...old,[type]:v}))}/>
    </div>)}
   {previews.transactions&&previews.settlements&&<div className="workspace-grid">
    {([["decimal","Dezimalformat",[["DE","1.234,56"],["DOT","1234.56"]]],
       ["date","Datumsformat",[["DE","TT.MM.JJJJ"],["ISO","JJJJ-MM-TT"]]],
       ["boolean","Gebucht-Kennzeichen",[["DE","Ja/Nein"],["EN","true/false"]]]] as const)
      .map(([key,label,options])=><label key={key}>{label}
       <select value={locale[key]} onChange={e=>setLocale(v=>({...v,[key]:e.target.value}))}>
        <option value="">Bitte wählen</option>
        {options.map(([code,text])=><option key={code} value={code}>{text}</option>)}
       </select></label>)}
   </div>}
  </fieldset>
  <fieldset disabled={busy||!previews.transactions||!previews.settlements}>
   <legend>4 · Vertragsregel und ERP-Kontrollbericht</legend>
   <p className="note">Pilotumfang: fester Bonusprozentsatz (FLAT_RATE) auf
    geprüfte Nettobuchungen. Hier werden ausschließlich eigene Vertragserkenntnisse bestätigt.</p>
   <label>ERP-Systemkennung<input value={sourceSystem} onChange={e=>setSourceSystem(e.target.value)}/></label>
   <div className="workspace-grid">
    {([["rule_id","Regel-ID"],["revision","Regelrevision"],
     ["supplier_id","Lieferanten-ID"],["agreement_id","Vertrags-ID"],
     ["period_start","Periode von (JJJJ-MM-TT)"],["period_end","Periode bis (JJJJ-MM-TT)"],
     ["rate","Bonusprozentsatz als Faktor (z. B. 0.02)"],
          ["source_revision","Dokumentenrevision"]] as const).map(([key,label])=>
      <label key={key}>{label}<input value={rule[key]}
       onChange={e=>{
        setRule(v=>({...v,[key]:e.target.value}));
        if(key==="rule_id"||key==="revision"||key==="agreement_id"||key==="source_revision"){
         setCandidateId("");setSegments([]);
        }
       }}/></label>)}
   </div>
   <button className="button-secondary" type="button" onClick={extractContract}>
    Vertragsfundstellen aus gescanntem PDF extrahieren
   </button>
   {candidateId&&<p>Dokumentkandidat: <code>{candidateId}</code>. Die
    automatische Extraktion ist keine Vertragsfreigabe.</p>}
   <label>Geprüfte Vertragsfundstelle
    <select value={rule.evidence} onChange={e=>setRule(v=>({...v,evidence:e.target.value}))}>
     <option value="">Belegstelle ausdrücklich auswählen</option>
     {segments.map((part,i)=><option value={part.evidence_ref} key={part.evidence_ref}>
      Seite {part.pages.join(",")||"?"} – Fundstelle {i+1}
     </option>)}
    </select>
   </label>
   {segments.filter(part=>part.evidence_ref===rule.evidence).map(part=>
    <p key={part.evidence_ref} className="note">{part.text}</p>)}
   <h3>Unabhängige ERP-Kontrollwerte</h3>
   <p className="note">Kontrollsummen aus einem separat erzeugten ERP-Bericht,
    nicht aus dem importierten Datensatz selbst.</p>
   <div className="workspace-grid">
    {([["tx_count","Einkäufe: kontrollierte Zeilen"],["tx_total","Einkäufe: Nettosumme (1234.56)"],
       ["tx_ref","Einkäufe: Kontrollreferenz"],["st_count","Gutschriften: kontrollierte Zeilen"],
       ["st_total","Gutschriften: Nettosumme (1234.56)"],
       ["st_ref","Gutschriften: Kontrollreferenz"]] as const).map(([key,label])=>
     <label key={key}>{label}<input value={control[key]}
      onChange={e=>setControl(v=>({...v,[key]:e.target.value}))}/></label>)}
   </div>
   <div className="workspace-confirmations">
    {([["tx","Einkaufsdaten für den Zeitraum vollständig"],
       ["st","Gutschriften für den Zeitraum vollständig"],
       ["agreements","Vertragsnachträge vollständig"],
       ["contract","Vertragsregel und Fundstelle persönlich kontrolliert"],
       ["mapping","Spaltenzuordnungen und Datentypen geprüft"]] as const)
      .map(([key,label])=><label key={key}><input type="checkbox" checked={review[key]}
       onChange={e=>setReview(v=>({...v,[key]:e.target.checked}))}/>{label}</label>)}
   </div>
   <button className="button-primary" type="button" onClick={approve}>
    Dokumentfundstelle bestätigen und signierte Prüfung registrieren
   </button>
   {bundle&&<p>Datenpaket: <code>{bundle}</code></p>}
  </fieldset>
  <fieldset disabled={busy||!bundle}><legend>5 · Bonusprüfung ausführen</legend>
   <button className="button-primary" type="button" onClick={calculate}>Audit berechnen</button>
   {audit&&audit.status==="COMPLETED"&&<div className="workspace-grid">
    <button type="button" className="button-secondary" onClick={()=>downloadReport("pdf")}>
     Kundenbericht PDF
    </button>
    <button type="button" className="button-secondary" onClick={()=>downloadReport("xlsx")}>
     Prüfbericht Excel
    </button>
    <button type="button" className="button-secondary" onClick={()=>downloadReport("json")}>
     Nachweise JSON
    </button>
   </div>}
   {audit&&<div className="info-block"><h3>Auditstatus: {audit.status}</h3>
    <p>Audit-ID: <code>{audit.audit_id}</code></p>
    {report&&<p>Erwartet: {String(report.expected_bonus_net??"—")} EUR.
     Verbucht: {String(report.recorded_bonus_net??"—")} EUR.
     <strong> Differenz: {String(report.difference_net??"nicht berechenbar")} EUR.</strong></p>}
    {readiness&&<p>Prüfstatus: <strong>{readiness.status||"Unbekannt"}</strong>.
     Datenabdeckung (Zeilen): {quality?.data_coverage_pct??"nicht bestimmbar"} %.
     Regelklarheit (signierte Semantik): {quality?.rule_clarity_pct??"nicht bestimmbar"} %.
     Kontrollsummen-Abgleich: {quality?.reconciliation_completeness_pct??"nicht bestimmbar"} %.</p>}
    {readiness?.issues?.map((issue,index)=><p key={issue.code+"-"+issue.field+"-"+index}
      className="note">{issue.severity}: {issue.code} ({issue.field}) – {issue.explanation}</p>)}
    {readiness&&<p className="note">Diese Quoten belegen keine Vollständigkeit der ERP-Quelldaten.
     Fehlende Kontrollwerte und fachliche Unklarheiten bleiben prüfpflichtig.</p>}
    <p className="note">Ein berechneter Betrag ist weder ein rechtlich
     festgestellter Anspruch noch eine tatsächlich zurückgewonnene Summe.</p>
   </div>}
  </fieldset>
  <fieldset disabled={busy||!audit||audit.status!=="COMPLETED"}>
   <legend>6 · Recovery und Honorar</legend>
   <button className="button-secondary" type="button" onClick={readLedger}>Ledger aktualisieren</button>
   {ledger&&<div className="info-block">
    <p>Bestätigt realisiert: <strong>{ledger.confirmed_realization_net} EUR</strong></p>
    <p>Honorarvorschlag ({(Number(ledger.fee_rate)*100).toLocaleString("de-DE")} %): <strong>{ledger.fee_proposal_net} EUR</strong></p>
    <p>Fällig / fakturiert: <strong>{ledger.fee_due_net} EUR</strong></p>
    {ledger.events.map(e=><p key={e.event_id}>{e.kind} · {e.amount_net} EUR ·
     {e.state} · <code>{e.event_id}</code></p>)}
   </div>}
   <div className="workspace-grid">
    <label>Nachweis-PDF<input type="file" accept=".pdf"
      onChange={e=>setFiles(v=>({...v,recovery:e.target.files?.[0]??null}))}/></label>
    <label>Ereignisart<select value={recoveryKind}
      onChange={e=>setRecoveryKind(e.target.value as "REALIZATION"|"REVERSAL")}>
      <option value="REALIZATION">Zusätzliche Realisierung</option>
      <option value="REVERSAL">Storno/Rückbuchung</option>
    </select></label>
    <label>Netto EUR (1234.56)<input value={recoveryAmount}
      onChange={e=>setRecoveryAmount(e.target.value)}/></label>
    {recoveryKind==="REVERSAL"&&<label>Referenz auf ursprüngliches Ereignis
      <input value={reversalId} onChange={e=>setReversalId(e.target.value)}/></label>}
   </div>
   <button type="button" className="button-secondary" onClick={reportRealization}>
    Realisierung mit Beleg zur unabhängigen Prüfung melden
   </button>
   <p className="note">Gemeldete Zahlungen zählen erst nach einer getrennten
    Finanzfreigabe. Es wird niemals automatisch eine Rechnung erstellt.</p>
  </fieldset>
  <fieldset disabled={busy||!audit||audit.status!=="COMPLETED"}>
   <legend>Fallstatus durch berechtigten Finanzprüfer</legend>
   <label>Status<select value={caseDirective}
    onChange={e=>setCaseDirective(e.target.value as "DISPUTED"|"CLOSED"|"OPEN")}>
    <option value="DISPUTED">Umstritten</option>
    <option value="CLOSED">Abgeschlossen</option>
    <option value="OPEN">Wiedereröffnen</option>
   </select></label>
   <label>Begründung<input value={caseReason}
    onChange={e=>setCaseReason(e.target.value)}/></label>
   <button type="button" className="button-secondary" onClick={markCaseStatus}>
    Fallstatus nachvollziehbar protokollieren
   </button>
  </fieldset>
  <fieldset disabled={busy}><legend>Separate Finanzfreigabe</legend>
   <p className="note">Nur mit eigenem Finance-Verifier-Zugriff,
    getrennt vom ursprünglichen Erfasser.</p>
   <div className="workspace-grid">
    <label>Recovery-Ereignis-ID<input value={financeEvent}
      onChange={e=>setFinanceEvent(e.target.value)}/></label>
    <label>Entscheidung<select value={financeDecision}
      onChange={e=>setFinanceDecision(e.target.value as "CONFIRM"|"REJECT")}>
      <option value="CONFIRM">Nach eigener Belegprüfung bestätigen</option>
      <option value="REJECT">Ablehnen</option>
    </select></label>
   </div>
   <button className="button-secondary" type="button" onClick={financeReview}>
    Finanzentscheidung dokumentieren
   </button>
  </fieldset>
 </div>;
}
