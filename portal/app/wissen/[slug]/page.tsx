import type {Metadata} from "next";
import Link from "next/link";
import {notFound} from "next/navigation";
import {articles,articleBySlug} from "../../../lib/content";
import {ConversionCTA} from "../../../components/ConversionCTA";
export function generateStaticParams(){return articles.map(a=>({slug:a.slug}));}
export async function generateMetadata({params}:{params:Promise<{slug:string}>}):Promise<Metadata>{
 const {slug}=await params;const article=articleBySlug(slug);
 return article?{title:article.title,description:article.description}:{title:"Artikel nicht gefunden"};
}
export default async function Article({params}:{params:Promise<{slug:string}>}){
 const {slug}=await params;const a=articleBySlug(slug);if(!a)notFound();
 return <><header className="page-hero"><Link className="back-link" href="/wissen">← Alle Artikel</Link>
 <span className="eyebrow">{a.category} · Fachbeitrag</span><h1>{a.title}</h1><p>{a.description}</p></header>
 <article className="content-page">{a.sections.map(s=><section key={s.heading}><h2>{s.heading}</h2>{s.paragraphs.map((p,i)=><p key={i}>{p}</p>)}</section>)}
 <p className="note">Fachlicher Überblick, keine Rechts- oder Steuerberatung. Aussagen über konkrete finanzielle Ansprüche erfordern die Prüfung der zugrunde liegenden Verträge und Buchungen.</p></article>
 <ConversionCTA/></>;
}
