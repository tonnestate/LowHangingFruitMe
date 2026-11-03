import type {Metadata} from "next";
import Link from "next/link";
import {articles} from "../../lib/content";
import {PageIntro} from "../../components/PageIntro";
import {ConversionCTA} from "../../components/ConversionCTA";
export const metadata:Metadata={title:"Wissen über Lieferantenboni, Margen und ERP-Daten",description:"Eigenständige Fachartikel zu Bonusstaffeln, Gutschriften, Finanzkontrollen und ERP-Automatisierung."};
export default function Knowledge(){return <><PageIntro eyebrow="Fachwissen" title="Wissen, das sich prüfen lässt." description="Hintergründe zu finanziellen Kontrollfragen, Datenqualität und der Grenze zwischen automatisierter Interpretation und verbindlicher Berechnung."/>
<section className="section divided-section"><div className="article-grid">{articles.map(a=><article key={a.slug} className="article-tile">
<span className="eyebrow">{a.category}</span><h2><Link href={"/wissen/"+a.slug}>{a.title}</Link></h2><p>{a.description}</p><Link href={"/wissen/"+a.slug}>Artikel lesen</Link></article>)}</div></section><ConversionCTA/></>}
