"use client";
import {useState} from "react";
import {feePreview} from "../lib/fee.mjs";

export function FeeCalculator(){
 const [value,setValue]=useState("25000");
 const result=feePreview(value);
 return <section className="calculator" aria-labelledby="calculator-title">
  <div><span className="eyebrow">Transparente Beispielrechnung</span>
   <h2 id="calculator-title">Was kosten 5 % Erfolgshonorar?</h2>
   <p>Tragen Sie einen rein beispielhaften, <em>bereits tatsächlich realisierten</em> zusätzlichen Nettobetrag ein. Das ist keine Prognose und keine automatische Abrechnung.</p></div>
  <div className="calculator-panel">
   <label htmlFor="recovery">Zusätzlich realisierter Nettobetrag in €</label>
   <input id="recovery" inputMode="decimal" autoComplete="off" value={value} onChange={e=>setValue(e.target.value)} aria-describedby="recovery-help"/>
   <small id="recovery-help">Dezimaltrennzeichen Komma oder Punkt; ohne Tausendertrennzeichen.</small>
   {result?<div className="calc-results" aria-live="polite">
    <div><span>Zusätzlich realisiert</span><strong>{result.input}</strong></div>
    <div><span>Erfolgsprovision (5 % netto)</span><strong>{result.fee}</strong></div>
    <div className="calc-result-main"><span>Verbleibt beim Kunden</span><strong>{result.customer}</strong></div>
   </div>:<p role="status">Bitte einen gültigen positiven Betrag eingeben.</p>}
   <p className="fineprint">Vor gegebenenfalls anfallender Umsatzsteuer auf unsere Provision. Nur eine Modellrechnung; Vertragsbedingungen werden vor dem Pilotbetrieb rechtlich geprüft.</p>
  </div>
 </section>;
}
