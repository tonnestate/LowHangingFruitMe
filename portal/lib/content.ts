export type ProductArea = {
  id: string; title: string; short: string; description: string;
  status: "Pilotvorbereitung" | "Konzept"; href: string;
};
export const productAreas: ProductArea[] = [
  {id:"rebates",title:"Lieferantenboni",short:"Bonusvereinbarungen mit Buchungen abgleichen",description:"Konditionen und Gutschriften auf berechenbare Differenzen untersuchen. Der technische Rechenkern ist vorhanden; eine öffentliche Kundenprüfung noch nicht.",status:"Pilotvorbereitung",href:"/lieferantenboni-pruefen"},
  {id:"margin",title:"Margenanalyse",short:"Ursachen für Margenabweichungen untersuchen",description:"Vertrags- und Verkaufspreise, Kostenänderungen und Rabatte künftig systematisch vergleichen.",status:"Konzept",href:"/margenanalyse"},
  {id:"payables",title:"Kreditorenkontrollen",short:"Rechnungs- und Gutschriftenabweichungen",description:"Rechnungspositionen und buchhalterische Nachweise künftig automatisiert abgleichen.",status:"Konzept",href:"/wissen/ki-und-erp-automatisierung"},
  {id:"receivables",title:"Debitorenprozesse",short:"Zahlungs- und Forderungsüberblick",description:"Abweichungen zwischen Rechnungen, Zahlungseingängen und offenen Posten künftig dokumentieren.",status:"Konzept",href:"/auftragsautomatisierung"},
  {id:"close",title:"Abschlusskontrollen",short:"Periodenübergreifende Prüfungen",description:"Buchungs- und Abstimmungsregeln für wiederkehrende Monatsabschlüsse als perspektivische Erweiterung.",status:"Konzept",href:"/wissen/automatisierung-voraussetzungen"},
  {id:"cost",title:"Kundenprofitabilität",short:"Wirtschaftlichkeit genauer verstehen",description:"Später Kunden- und Auftragsbeiträge mit überprüfbaren Kostentreibern verbinden.",status:"Konzept",href:"/margenanalyse"},
  {id:"stock",title:"Bestandsintelligenz",short:"Gebundenes Kapital und Abweichungen",description:"Perspektivische Bestandskontrollen für Unternehmen mit geeigneten ERP-Daten.",status:"Konzept",href:"/serviceumsatz"}
];
export const nav = [
  {href:"/lieferantenboni-pruefen",title:"Lieferantenboni"},
  {href:"/margenanalyse",title:"CFO & Marge"},
  {href:"/auftragsautomatisierung",title:"Auftragsprozesse"},
  {href:"/serviceumsatz",title:"Service"},
  {href:"/wissen",title:"Wissen"},
  {href:"/preis-und-ablauf",title:"3 % Erfolgsmodell"}
];
export type Article = {slug:string,title:string,description:string,category:string,sections:{heading:string,paragraphs:string[]}[]};
export const articles: Article[]=[
  {
    slug:"margenverluste-im-grosshandel",title:"Warum hohe Umsätze nicht automatisch hohe Margen bedeuten",
    description:"Vier kaufmännische Kontrollfragen für Einkaufs- und Vertriebsorganisationen.",category:"Finanzsteuerung",
    sections:[
      {heading:"Konditionen sind nicht dasselbe wie Buchungen",paragraphs:["Eine verhandelte Rückvergütung ist noch kein verbuchter wirtschaftlicher Vorteil. Prüfen Sie, ob die Gutschrift auf dieselbe Lieferantenvereinbarung, Periode und berechtigte Umsatzbasis verweist.","Fehler entstehen besonders dann, wenn Retouren, Nachträge und unterschiedliche Vertragsperioden nicht eindeutig zugeordnet werden."]},
      {heading:"Veränderungen der Einkaufskosten",paragraphs:["Preislisten und tatsächliche Einkaufspreise sollten über dieselben Warengruppen und Gültigkeitszeiträume verglichen werden. Ohne belastbare Artikelzuordnung ist eine automatisierte Aussage über Margenverluste nicht seriös."]},
      {heading:"Rabatte und Sonderkonditionen",paragraphs:["Unterschiedliche Freigaben können die erzielte Marge verändern. Ein Prüfwerkzeug muss unterscheiden, ob eine Abweichung vertraglich erlaubt, bewusst genehmigt oder tatsächlich ungeklärt ist."]},
      {heading:"Was ein sinnvoller erster Prüfauftrag braucht",paragraphs:["Beginnen Sie mit einem Lieferanten, einem abgeschlossenen Zeitraum und einem klar zuordenbaren Bonusprogramm. Ein auditierbarer Ausgangsbestand ist wichtiger als eine möglichst große Zahl importierter Dateien."]}
    ]
  },
  {
    slug:"kosten-manueller-auftragserfassung",title:"Manuelle Auftragserfassung: Welche Kosten sind messbar?",
    description:"Eine sachliche Betrachtung von Bearbeitung, Korrekturen und Nacharbeit.",category:"Prozesse",
    sections:[
      {heading:"Bearbeitungszeit dokumentieren",paragraphs:["Zeitaufwände sollten je Auftragsart und Bearbeitungsschritt erfasst werden, statt eine pauschale Zeitersparnis aus anderen Unternehmen zu übernehmen."]},
      {heading:"Korrekturen separat bewerten",paragraphs:["Fehlartikel, doppelte Anlage, Rückfragen und manuelle Freigaben erzeugen unterschiedliche Aufwände. Ein sauberer Prozessvergleich erfasst deren tatsächliche Häufigkeit und Folgekosten."]},
      {heading:"Automatisierung ist noch kein Geschäftsfall",paragraphs:["Erst mit vollständigen Ausgangsdaten und klar definierten Freigaben lässt sich entscheiden, welcher Arbeitsschritt regelbasiert automatisiert werden kann."]}
    ]
  },
  {
    slug:"ki-und-erp-automatisierung",title:"KI und ERP-Automatisierung: Wo die Grenzen liegen",
    description:"Warum Interpretation und verbindliche Finanzberechnung getrennt gehören.",category:"Technologie",
    sections:[
      {heading:"KI unterstützt die Datenerkennung",paragraphs:["Aus heterogenen Exporten lassen sich Spalten und Dokumenttypen vorschlagen. Eine plausible Zuordnung ersetzt aber keine Bestätigung von Währung, Vertrag, Zeitraum oder Lieferant."]},
      {heading:"Beträge brauchen deterministische Regeln",paragraphs:["Eine finanzielle Differenz muss sich mit derselben Vertragsregel und denselben Buchungen wiederholt gleich berechnen lassen. Deshalb wird die Betragsrechnung nicht an ein Sprachmodell delegiert."]},
      {heading:"Das ERP bleibt führend",paragraphs:["Ein externer Prüfdienst kann lesende Exporte verarbeiten und eigene Differenzakten erstellen. Er muss dafür weder Rechnungen im ERP ändern noch Geschäftsvorfälle automatisch buchen."]}
    ]
  },
  {
    slug:"margenanalyse-prueffelder",title:"Fünf Datenfragen vor einer kaufmännischen Margenprüfung",
    description:"Vertragsbasis, Buchungsstatus, Retouren, Gutschriften und Datenumfang.",category:"Praxis",
    sections:[
      {heading:"1. Ist die Vertragsperiode vollständig?",paragraphs:["Für einen Jahresbonus reichen drei Monate Einkaufsdaten meist nicht. Benötigt wird die vertraglich definierte Periode einschließlich späterer Korrekturen."]},
      {heading:"2. Welche Beträge sind bonusfähig?",paragraphs:["Steuern, Fracht, Retouren und Skonti dürfen nicht nach Bauchgefühl ein- oder ausgeschlossen werden. Die Regel muss aus einer nachgewiesenen Klausel stammen."]},
      {heading:"3. Sind Gutschriften eindeutig zugeordnet?",paragraphs:["Eine Gutschrift ohne Vertrags- oder Periodenbezug darf nicht automatisch von einem berechneten Bonus abgezogen werden."]},
      {heading:"4. Gibt es unabhängig erzeugte Kontrollwerte?",paragraphs:["Ein Separatbericht aus dem ERP mit Zeilenanzahl und Nettosumme kann den Import plausibilisieren. Das beweist noch keine vollständige Buchhaltung."]},
      {heading:"5. Wer prüft die Regel?",paragraphs:["Ein dokumentierter Prüfer muss der konkreten Vertragsfassung und der daraus abgeleiteten Berechnung zustimmen. Ein einfacher Freigabe-Schalter genügt nicht."]}
    ]
  },
  {
    slug:"automatisierung-voraussetzungen",title:"Wann ist eine automatisierte Finanzprüfung sinnvoll?",
    description:"Eine kurze Checkliste für Datenverfügbarkeit und prüfbare Regeln.",category:"Checkliste",
    sections:[
      {heading:"Die Mindestvoraussetzungen",paragraphs:["Es existieren schriftliche, eindeutig berechenbare Lieferantenkonditionen. Einkaufs- und Gutschriftendaten sind elektronisch verfügbar. Der betroffene Zeitraum und die zuständige Gesellschaft sind bekannt."]},
      {heading:"Mit einer kleinen Stichprobe beginnen",paragraphs:["Ein einzelner abgeschlossener Bonusfall ist aussagekräftiger als ein breiter Upload unbekannter Datenqualität. Sind die Quellen unvollständig, muss der Prüfstatus diese Einschränkung sichtbar machen."]},
      {heading:"Sicherheit zuerst",paragraphs:["Vertragsunterlagen und Einkaufsdaten können Geschäftsgeheimnisse enthalten. Vor einer Übertragung müssen Zweck, technische Schutzmaßnahmen und Zugriffsrechte geregelt sein."]}
    ]
  }
];
export const articleBySlug = (slug:string) => articles.find(a=>a.slug===slug);
