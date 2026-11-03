import Link from "next/link";
export function ConversionCTA({title="Klären, ob eine Bonusprüfung sinnvoll ist."}:{title?:string}){
 return <section className="cta-band" aria-labelledby="cta-title"><div className="main-container cta-band-inner">
  <div><span className="eyebrow">Pilotvorbereitung</span><h2 id="cta-title">{title}</h2><p>Kein automatischer Forderungseinzug und kein Upload von Finanzdaten auf dieser Website.</p></div>
  <Link className="button-primary" href="/eignungscheck">Eignungscheck ansehen</Link>
 </div></section>;
}
