# LowHangingFruitMe – Vertrags-, Vergütungs- und Compliance-Konzept v0.1

**Stand:** 02.11.2026 | **Status:** fachlicher Vertragsentwurf / KEINE Rechtsberatung / vor Markteintritt juristisch freigeben.

## 1. Vier getrennte Rechtsverhältnisse

**(1) LowHangingFruitMe ↔ B2B-Kunde:** Dienstvertrag über technische und kaufmännische Datenprüfung sowie Erstellung beleggestützter Differenzakten. Vertrag spezifiziert Unternehmen, Zeitraum, Lieferanten/Verträge, Datenverarbeitung, Mitwirkung und Erfolgsentgelt.

**(2) Kunde ↔ Lieferant:** bestehender Lieferanten- und Bonusvertrag. LowHangingFruitMe übernimmt keine Forderung, wird kein Vertreter des Kunden gegenüber Lieferanten, nimmt kein Lieferantengeld entgegen und betreibt im MVP keine eigenständige Einziehung.

**(3) LowHangingFruitMe ↔ ERP-Marktplatz:** eigenständige Teilnahme-/Listing-/API-/Markennutzungsvereinbarungen. Ein Listing ist nicht automatisch die Erlaubnis, externe erfolgsabhängige Gebühren zu erheben.

**(4) LowHangingFruitMe ↔ Auftragsverarbeiter:** Hosting und ggf. andere Dienstleister brauchen adäquate Vertraulichkeit, Sicherheit und bei einschlägiger Verarbeitung personenbezogener Daten Art.-28-DSGVO-Verträge.

## 2. Für den Start erforderliche Vertragsunterlagen

- B2B-Leistungsschein: genaue Gesellschaft, Prüfzeitraum, Bonusarten, Lieferanten, zugelassene Quelldaten, Ergebnislieferung, Ausschlüsse.
- B2B-AGB/Dienstleistungsvertrag: Rechte und Pflichten, Vertretungsbefugnis, Datenberechtigung, Qualität und Grenzen, Belegbereitstellung, Haftung, Vertraulichkeit, Laufzeit, Beendigung, Datenlöschung, Konflikte.
- Erfolgshonorar-Anlage: Basis, Satz, Attribution, Nachweis, Vorbekanntheit, Teil-/Storno-Realisierung, Fälligkeit, Nachlauf und Einwendungen.
- Datenschutzhinweise, TOMs und gegebenenfalls AVV mit Unterauftragnehmerliste.
- Versioniertes digitales Annahmeprotokoll: Vertragstext-Hash, Timestamp, Akteur, Unternehmen, Rollen-/Vertretungsbestätigung, zugeordneter Auftrag, Zustimmung zur Kostenregel. Ob dieser Formnachweis genügt, wird juristisch geprüft.

Eine vollständige externe E-Signature-Plattform ist nicht notwendig, solange für die konkrete B2B-Vereinbarung eine wirksame und beweisbare elektronische Annahme ausreicht. Keine eigenmächtige Behauptung über Formfreiheit oder Signaturwert.

## 3. Verkaufte und ausgeschlossene Leistung

**Verkauft:** Datenimport, strukturelle Vertragsklausel-Erkennung, berechenbare Bonusregeln, quantitativer Vergleich, kaufmännische Differenzakte, interne Nachweisdokumente, Recovery-Monitoring und vereinbarte Erfolgsabrechnung.

**Nicht verkauft:** rechtsverbindliche Anspruchsentscheidung, professionelle Rechtsvertretung, eigene Inkassotätigkeit, automatisches Lieferantenschreiben in unserem Namen, Forderungskauf, garantierte Rückgewinnungsquote oder Erfolgsgarantie.

Marketingaussagen wie „1–3 % des Umsatzes“ sind nur nach eigener belastbarer Validierung oder als klar gekennzeichnete Aussage eines anderen Anbieters verwendbar.

## 4. Erfolgshonorar – Bemessung und Zurechnung

**Verbindliche Produkt-Preisentscheidung (vertraglich noch zu prüfen):** 3 % × der **nachgewiesenen, zusätzlich, kausal aufgrund unserer dokumentierten Findings realisierten und nicht anderweitig bereits vergüteten Netto-Lieferantenvergütung**. Unser Honorar kann seinerseits umsatzsteuerpflichtig sein.

Abrechenbar nur, wenn:
1. Ein dokumentierter Case innerhalb des angenommenen Leistungsscheins existiert.
2. Der wirtschaftliche Vorteil sich nachweislich auf einen bezeichneten Lieferanten, Vertrag, Zeitraum und Case bezieht.
3. Der Anspruch vor Vertragsbeginn nicht bereits eigenständig ermittelt und aktiv bearbeitet worden war, sofern ausdrücklich anders vereinbart.
4. Der Kunde die zusätzliche Vergütung tatsächlich erhalten oder wirtschaftlich wirksam verrechnet hat.
5. Derselbe Vorgang nicht doppelt gezählt wird – etwa Gutschrift und anschließender Zahlungseingang als zwei getrennte Boni.
6. Rückbuchungen/Korrekturen rückwirkend den realisierten Nettobetrag und ggf. unsere Gebühr mindern.

**Beispiel, keine Prognose:** ermittelte Differenz 36.700 EUR; Zusatzgutschriften werden für 12.000 EUR anerkannt; davon sind 8.000 EUR zugeflossen und 4.000 EUR wirksam verrechnet. Ergebnis bei vollständig geprüfter Zuordnung: 12.000 EUR Realisierung, 360 EUR netto Honorar vor USt. Auf nicht realisierte 24.700 EUR wird nichts berechnet.

**Definition von Realisierung** vor Unterschrift: Zahlung, endgültig wirksame Verrechnung oder unter klar bestimmten Voraussetzungen endgültig nutzbare und belegte Gutschrift. Eine bloße Lieferantenzusage oder von uns berechneter Anspruch genügt nicht.

## 5. Nachweisbuch und Kundenmitwirkung

Jede Finding-ID hat ein lückenloses Recovery-Ledger. Eingänge: Lieferantengutschrift, Zahlungsavis und Bankzuordnung, buchhalterischer Verrechnungssatz, Stornobeleg, schriftliche Lieferantenantwort (nur als ergänzender Nachweis). Zustände unterscheiden DRAFT, SUPPLIER_ACCEPTED, REALIZED_PARTIAL, REALIZED_FULL, REVERSED und DISPUTED; keine Doppelerfassung.

Die B2B-Vereinbarung sollte eine **angemessene und zweckgebundene Pflicht zur Mitteilung von nachgelagerten wirtschaftlichen Erfolgen** sowie Verifikation anhand beschränkter Belege enthalten. Bei vereinbarten ERP-Connectoren ausschließlich autorisierte Read-only-Buchungsabgleiche. Keine unbegrenzten Betriebsprüfungsrechte oder pauschale Einsicht in fremde Finanzdaten. Sanktionen, Ersatzauskunft und Nachprüfungsrechte müssen auf Wirksamkeit und Verhältnismäßigkeit geprüft werden (insbesondere BGB-AGB-Kontrolle).

Als Arbeitsvorschlag: 12 Monate Nachlauf für konkret dokumentierte Cases, nicht für sämtliche künftigen Lieferantenzahlungen. Dieser Wert ist **keine gesetzliche Frist** und rechtlich/geschäftlich noch zu validieren.

## 6. Unser tatsächlicher Zahlungsfluss

1. Kunde registriert sich und nimmt rechtsverbindlich den Leistungsschein mit Erfolgshonorar an.
2. Audit und Report erzeugen ein Einzelverzeichnis von Fall-IDs.
3. Kunde klärt die Differenzen beim Lieferanten selbst.
4. Der Kunde meldet realisierte Zahlungen/Gutschriften/Verrechnungen oder stellt einen autorisierten Buchungsabgleich bereit.
5. Der Recovery-Ledger berechnet einen Beleg-basierten Gebührenvorschlag.
6. Betreiber prüft und gibt Rechnung frei; der Kunde erhält eine ordentliche B2B-Rechnung.
7. Kunde zahlt per Überweisung/SEPA auf unser Konto; ERP-/Bank-Abgleich verbucht Zahlungseingang.
8. Teilzahlungen und Storno führen zu Korrekturen; Rechnungskorrekturen werden nicht blind automatisiert.

**Wichtig:** Wir verwalten niemals Gelder, die dem Kunden vom Lieferanten zustehen. Nur unsere eigene Honorarrechnung geht an den Kunden. Für das MVP braucht es **keinen** Stripe-Checkout oder eine komplexe Abo-Billing-Plattform; vorhandene legale Rechnungserstellung genügt.

## 7. Marktpartner und App-Store-Verträge

**Lexware Office:** Technologiepartnerprogramm verlangt eigenes funktionsfähiges Softwareprodukt, Webpräsenz und Kundensupport; Partner-API und Listing nach Onboarding. Der offizielle Prozess umfasst Build, Deliver, Silent Launch, Launch, Grow; der reguläre Build-Abschnitt ist mit 8–10 Wochen angegeben. Partnergebühren laut veröffentlichter Übersicht keine, aber Entwicklungs- und Supportaufwand bleibt.

**Odoo:** App-Store-Veröffentlichung mit eigenen Regeln. Externes Success-Fee-Billing über unsere Website darf nicht als erlaubte Praxis unterstellt werden. Ein kostenloses Connector-Modul mit kostenpflichtiger Remote-API bedarf einer vorab verifizierten Richtlinienfreigabe.

**Frappe/ERPNext:** Marktplatz-App muss laut offizieller Anleitung öffentlich auf GitHub und offen/GPL-kompatibel sein; gesondert betriebene API und die Zulässigkeit ihrer Abrechnung müssen geprüft werden.

**Dolibarr/Oro:** konkrete Publisher- und kommerzielle Integrationsbedingungen vor Start eines spezifischen Connector-Projekts verifizieren. Keine Annahme, dass alle Marktplätze dieselbe Vergütungstechnik erlauben.

### Akquisitionsentscheidung

Marktplatz ist ein Kanal zur Installation/Discovery. Das wirtschaftliche Produkt bleibt der **direkte LowHangingFruitMe-Prüfvertrag**. Keine Integration darf die Kundendaten oder die Bonusengine vollständig einem Marktplatzbetreiber überlassen.

## 8. RDG und Forderungsdurchsetzung – harter Go-live-Blocker

§ 2 RDG erfasst konkrete Rechtsprüfung fremder Angelegenheiten und bei eigenständig betriebenem Einzug fremder Forderungen die Inkassodienstleistung; § 10 RDG betrifft hierfür erforderliche Registrierungen. Die tatsächliche Tätigkeit zählt, nicht das Etikett „AI Software“.

Daher im MVP:
- keine eigenständige anwaltliche Beratung oder streitige Rechtsauslegung im konkreten Fall,
- kein autonomer Lieferantenkontakt in unserem Namen, keine Abtretung und keine Inkassovollmacht,
- ausschließlich rechnerische, quellengebundene Analyse und kaufmännische Unterlagen, die der Kunde selbst verwendet,
- bei fehlender eindeutiger Vertragsklausel: Daten-/Rechtsklärung notwendig, nicht verbindlich berechenbar.

Eine spezialisierte rechtliche Prüfung muss den tatsächlichen Leistungsinhalt (inklusive Erfolgshonorar, Vertragstext, Case-Reports und Marketing) vor dem ersten zahlenden Kunden beurteilen. Ggf. wird der Leistungsumfang eingeschränkt oder eine zulässige Partnerschaft benötigt.

## 9. Verjährung, steuerliche und handelsrechtliche Themen

Die gesetzliche Regelverjährung beträgt nach § 195 BGB drei Jahre; § 199 BGB bestimmt den regulären Beginn. Vertragliche Ausschlussfristen, Bonusvereinbarungen, Gesellschaften, Hemmung und Spezialnormen können zu anderen Ergebnissen führen. Der Agent darf höchstens einen Fristenhinweis mit Quelle und Ungewissheit ausgeben; keine verbindliche Verjährungsentscheidung.

Für Umsatzsteuer-/Buchungsbehandlung von Lieferantenboni, Gutschriften und unserem Leistungshonorar sowie Aufbewahrungs- und Rechnungsanforderungen ist fachkundige steuerliche Prüfung erforderlich. Abrechenbare Realisierung und buchhalterische Gutschrift können auseinanderfallen; beide Daten getrennt speichern.

## 10. Datenschutz, Geschäftsgeheimnisse, Informationssicherheit

Kunden müssen Rechte zum Upload und Datenanschluss nachweisen; Finanzdaten sind Geschäftsgeheimnisse und ggf. personenbezogen. Bei Art.-28-DSGVO-Auftragsverarbeitung AVV, TOMs und Subdienstleisterregelung. Technisch: private verschlüsselte Speicherung, TLS, strikte Tenant-Isolation, Rollen, Audit-Log, minimierte Rechte, definierte Löschung/Retention, Schutz vor Prompt Injection und Verbot unautorisierter externer KI-Abflüsse.

**Nicht im öffentlichen GitHub-Repo:** Kundenverträge, Buchungsbelege, Lieferantennamen aus Kundenkonten, Zugriffsschlüssel, produktive Datenbankdumps oder private FruitStack-Implementierungsdetails.

## 11. Rechtliche Abnahmekriterien

- [ ] RDG-/Leistungsabgrenzung durch qualifizierte juristische Prüfung bestätigt.
- [ ] Leistungs-/Erfolgshonorarvertrag und Attribution transparent und wirksam.
- [ ] angemessene Meldepflicht/Nachweis-/Korrekturklausel geprüft.
- [ ] Vertretungsrecht und digitale Annahme beweisbar.
- [ ] Datenschutzrollen, AVV und TOMs abgeschlossen soweit nötig.
- [ ] App-Store-Billing/Listing- und Markenbedingungen je Connector geklärt.
- [ ] eigene Rechnungsstellung, USt und Zahlungseingang geprüft.
- [ ] Verjährung/Ausschlussfristen als ungewisse Fachwarnung behandelt.

## 12. Quellen

- https://www.gesetze-im-internet.de/rdg/__2.html
- https://www.gesetze-im-internet.de/rdg/__10.html
- https://www.gesetze-im-internet.de/bgb/__195.html
- https://www.gesetze-im-internet.de/bgb/__199.html
- https://www.gesetze-im-internet.de/bgb/__307.html
- https://eur-lex.europa.eu/eli/reg/2016/679/oj
- https://www.lexware.de/partner/modelle/
- https://docs.frappe.io/cloud/marketplace/publishing-an-app-to-marketplace

Diese Datei ist **kein unterschriftsreifer Vertrag und keine rechtsverbindliche Einzelfallberatung**.

## Zusätzliche externe Abnahme vor erstem zahlenden B2B-Kunden (03.11.2026)

Eine auf RDG und B2B-Vertragsgestaltung spezialisierte **externe** Rechtsprüfung ist zwingender kommerzieller Freigabeschritt. Der Gutachter prüft schriftlich:

1. Welche rein technische bzw. kaufmännische Datenauswertung ohne Rechtsdienstleistung erbracht werden kann und ab wann individuelle Anspruchsprüfung beginnt.
2. Ob und unter welchen Bedingungen die **3%-Erfolgsvergütung** für die konkrete Leistung wirksam vereinbart werden kann, insbesondere Zurechenbarkeit, nachgelagerte Teil-/Storno-Realisierungen und Rechnungsfreigabe.
3. Ob zulässige Supportleistungen, Vertragserläuterungen, Lieferantenkontakte und Kundenhilfen bereits regulierte Rechtsdienstleistung bzw. Inkasso wären. Bis zur Abnahme bleibt LowHangingFruitMe strikt auf Datenprüfung und vom Kunden selbst gesteuerte Klärung begrenzt.
4. Rechtmäßige Bereitstellung geschäfts- und personenbezogener Einkaufsdaten, AVV/TOMs, Aufbewahrung, Löschung und Schutz von Lieferantengeheimnissen.
5. Dokumentation der unterzeichneten schriftlichen Rechts- und Datenschutz-Freigabe, versioniert zum konkreten Pilotvertrag.

Die externe Prüfung **liegt noch nicht vor**. Ein Code-Test kann weder eine Rechtsfreigabe noch echte Forderungsrealisierung nachweisen.
