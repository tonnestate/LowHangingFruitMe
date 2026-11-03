"use client";
import {useState} from "react";
import Link from "next/link";
import {productAreas} from "../lib/content";
export function AgentExplorer(){
 const [selected,setSelected]=useState<string[]>(["rebates"]);
 return <section className="section" id="prueffelder" aria-labelledby="agent-title">
  <div className="section-heading"><span className="eyebrow">Die finanzielle Kontrolllandschaft</span>
   <h2 id="agent-title">Sieben mögliche Prüffelder. Ein klarer Start.</h2>
   <p>Der Bonus-Audit ist unser erster technischer Produktkern. Die übrigen Felder zeigen die geplante Entwicklung, nicht sieben bereits laufende KI-Agenten.</p>
  </div>
  <div className="agent-grid">{productAreas.map((area,index)=><article className="agent-card" key={area.id}>
   <div className="agent-meta"><span className="agent-index">{String(index+1).padStart(2,"0")}</span><span className={area.status==="Konzept"?"status roadmap":"status"}>{area.status}</span></div>
   <h3>{area.title}</h3><p>{area.short}</p>
   <p className="agent-description">{area.description}</p>
   <div className="agent-actions">
    <label className="agent-choice"><input type="checkbox" checked={selected.includes(area.id)} onChange={e=>setSelected(current=>e.target.checked?[...current,area.id]:current.filter(v=>v!==area.id))}/> Interesse markieren</label>
    <Link href={area.href}>Mehr erfahren</Link>
   </div>
  </article>)}</div>
  <div className="interest-summary" role="status">Vorgemerkte Themen: {selected.length} von {productAreas.length}. Diese Auswahl ist nur lokal in Ihrem Browser, wird nicht übertragen und aktiviert keine Softwarefunktion.</div>
 </section>;
}
