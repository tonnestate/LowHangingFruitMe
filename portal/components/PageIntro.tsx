import Link from "next/link";
export function PageIntro({eyebrow,title,description,development=false}:{eyebrow:string;title:string;description:string;development?:boolean}){
 return <header className="page-hero">
   <span className="eyebrow">{eyebrow}</span>
   {development&&<span className="status roadmap">Fachkonzept · nicht buchbar</span>}
   <h1>{title}</h1><p>{description}</p>
   {!development&&<div className="action-row"><Link className="button-primary" href="/eignungscheck">Eignungscheck</Link><Link className="button-secondary" href="/preis-und-ablauf">Preis & Ablauf</Link></div>}
 </header>;
}
