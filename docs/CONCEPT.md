# LowHangingFruitMe – verbindliches fachliches und technisches Konzept v0.1

**Stand:** 02.11.2026 | **Status:** Zielarchitektur / Research-Baseline, keine Implementierung | **Produktverantwortung:** eigenständiges FruitStack-Schwesterprodukt

## 0. Auftrag, Ergebnis und harte Grenzen

LowHangingFruitMe findet aus Kundendaten bereits wirtschaftlich entstandene, aber nicht oder nicht vollständig gutgeschriebene Lieferantenboni und andere **vertraglich eindeutig berechenbare** Einkaufsvergütungen. Das Produkt liefert eine prüfbare Differenzakte und verfolgt nach Kundeneingabe oder autorisiertem Buchungsabgleich, ob daraus tatsächlich zusätzlicher wirtschaftlicher Nutzen wurde. Es berechnet ausschließlich anhand dokumentierter Vertragsregeln und belegter Transaktionen. Eine KI darf Klauseln erfassen, Abgleichsvorschläge liefern und begründen; die KI darf weder rechnerische Ansprüche erfinden noch rechtliche Forderungen verbindlich feststellen.

**Nicht im v0.1-Scope:** autonomes Inkasso, eigenständige Verhandlungen mit Lieferanten, Forderungskauf, Auszahlung/Entgegennahme von Lieferantengeldern, automatisches Verbuchen von Gutschriften, vollautomatische juristische Vertragsauslegung, allgemeine Rechnungsaudit- oder ERP-Plattform, ein weiteres zentrales FruitStack-Memory oder ein weiterer Agenten-Orchestrator.

**Wettbewerbshypothese:** Erfolgshonorar-Audits sind nicht neu; insbesondere revotail kommuniziert bereits Rebate-Recovery-Leistungen. Differenzierung kann deshalb nicht allein „keine Grundgebühr, 3 % Erfolg“ sein, sondern wäre ein überprüfbares, eingebettetes, selbst bedienbares Produkt mit revisionsfähiger Nachweiskette, wiederverwendbarer API und ERP-Distribution. Noch **nicht** durch zahlende Kunden belegt.

## 1. Geschäftlicher Anwendungsfall

**Ideal Customer Profile – zu validierende Hypothese:** B2B-Großhändler, Teilehandel, technischer Handel, Baustoff-/Elektro-/Sanitärgroßhandel, Handelsverbünde und Einkaufsorganisationen mit wiederkehrenden Lieferantenkonditionen, mehreren Bonusvereinbarungen und elektronischen Transaktionsdaten. Nicht jeder Lexware-Office-Kunde ist die Zielgruppe; reine Kleinunternehmer ohne komplexe Lieferantenboni sind häufig ungeeignet. Erstkunden nur bei vorhandener Datenbasis und namentlich verantwortlichem Einkaufs-/Finance-Ansprechpartner.

**Einstiegsangebot:** einmalige Prüfung einer abgeschlossenen Abrechnungsperiode (zunächst ein Unternehmen, ein Lieferant, ein Vertrag, ein Jahr). Gefordert sind Vertrag/Anhänge/Nachträge, vollständige Einkaufsdaten, erhaltene Bonusgutschriften und ggf. Retouren/Korrekturen. Weitere Exporte werden bei Datenlücken angefordert.

**Zielergebnis:** keine bloße Tabelle, sondern je möglicher Differenz ein eindeutiger Case mit (a) Rechts-/Vertragsquelle als Originalzitat mit Fundstelle, (b) normalisierter Regel, (c) prüfbar definiertem Berechnungsumfang, (d) berechneter Brutto-/Netto-/Bonusbasis, (e) Abgleich mit bereits erfassten Gutschriften/Verrechnungen, (f) Datenqualitätsstatus, (g) Kopie/Referenz der Quelltransaktionen und (h) nachfolgenden Buchungsnachweisen für die Erfolgsvergütung.

## 2. Bonusklassen und genaue Rechenbasis

**R1 – fester Jahresumsatzbonus:** Prozentsatz auf vertraglich definierte bonusfähige Nettobezugsbasis des Lieferanten im Zeitraum. Exakte Definition der Basis (Bestellungen, Rechnungen, Wareneingang, Retoure, Fracht, Steuern, Skonti, Storno) wird pro Vereinbarung hinterlegt.

**R2 – Schwellenstaffel:** Bonusprozentsatz oder Fixbetrag abhängig von Umsatzschwellen. Die Klausel muss unterscheiden, ob eine erreichte Stufe rückwirkend auf den gesamten relevanten Umsatz, nur auf den Schwellenüberschuss oder differenziert auf Umsatzscheiben gilt. Ohne diese Information keine automatische Berechnung.

**R3 – Artikel-/Warengruppenbonus:** nur für nachweislich klassifizierte SKU/Warengruppen, inklusive Gültigkeitsdauer, Lieferanten-Artikelmapping und Ausschlüsse.

**R4 – Wachstums-/Vorjahresbonus:** v0.2 nach Nachweis vollständiger und vergleichbarer Vorperioden sowie Änderung von Firma, Geschäftsjahr, Kontenstruktur und Vertragsdefinition.

**R5 – Ziel-, Quartals-, Filial-, Verbund-/Rückvergütungsregeln:** spätere Releases, abhängig von erforderlichen zusätzlichen Granularitäten und Partnergruppen.

**Noch nicht eigenständig v0.1:** Marketing-/Werbekostenzuschüsse, Zielvereinbarungen mit Ermessenskomponente, beschädigte Ware, Skonto- oder Preiseinzelfall-Streitigkeiten, Rabatte ohne eindeutige Anspruchsklausel, allgemeine Debitoreninkasso-Fälle.

**Priorität für den ersten echten Fall:** R1 mit einer eindeutigen umsatzbasierten Formel. Damit sind die Anspruchsgrundlage und der Buchungsabgleich vergleichsweise gut testbar.

## 3. Kundenreise und UX ohne Plattformneubau

1. Öffentliche Landingpage erläutert Leistung, Belegbedarf, Vergütung, Vertragsabgrenzung, Datenschutz und Ergebnisbeispiel. Keine unbelegten Recovery-Prozentsätze.
2. Unternehmen registriert sich, bestätigt Vertretungsberechtigung und verifiziert seine E-Mail. Rollen: Organisation-Admin, Uploader, Prüfer, nur Lesen.
3. Auftrag definiert Lieferant, Abrechnungsperiode, juristische Einheit und Verwendungszweck; Vertrag/AGB/Leistungsschein, Datenschutz und erforderlichenfalls AV-Vertrag sind vor Freigabe des vollständigen Audits angenommen und versioniert.
4. Upload: PDF, PDF/A, CSV, XLSX, XML, ZIP (mit Größen-/Entpacklimits), alternativ autorisierte Datenübertragung per API oder Connector.
5. System erkennt Dokumenttyp und Tabellenfelder, zeigt Zuordnungen und unverstandene Klauseln; Kunde bestätigt nur notwendige Unsicherheiten.
6. Audit erzeugt nachvollziehbare Fallliste: CONFIRMED_DATA_DIFF, NEEDS_DATA, NEEDS_REVIEW, NO_DIFFERENCE oder NOT_CALCULABLE. „CONFIRMED_DATA_DIFF“ ist **keine juristisch bestätigte Forderung**.
7. Exporte: vollständiger interner Prüfbericht als PDF, XLSX und JSON; kaufmännische Differenzaufstellung für den eigenen Versand durch den Kunden.
8. Recovery-Ledger verfolgt offene/akzeptierte/abgelehnte/teilweise realisierte Positionen. Der Kunde meldet Gutschriften oder stellt begrenzten lesenden Buchungszugang bereit.
9. Nach belastbarem Nachweis des wirtschaftlichen Zuflusses/der Verrechnung wird eine zugehörige Erfolgsabrechnung vorbereitet und nach Rechnungsfreigabe fakturiert.

**Keine Mogel-Automation:** fehlende Daten dürfen keinen „100 % geprüft“-Status erzeugen; Modellschätzungen dürfen nicht als vertraglicher Anspruch ausgewiesen werden.

## 4. Systemarchitektur und FruitStack-Grenzen

Architekturprinzip: **eine fachliche API + eine Rechenengine + ein Recovery-Ledger**, ERP-spezifische Adapter nur an der Grenze. Keine Kopie ganzer ERP-Server, keine weitere Golden-Record-Instanz, keine allgemeine SaaS-Verwaltungsplattform.

- **Portal:** eigenständige LowHangingFruitMe-Webanwendung mit getrenntem Backend und eigener Auth-/Mandantenschicht. Keine TonnEstate-WordPress-UI und keine ungeprüfte Abhängigkeit von TonnEstate-Tabellen. Das endgültige Frontend-Framework ist vor Implementierung anhand bereits genutzter FruitStack-Web-Komponenten auszuwählen.
- **API:** Python/FastAPI als begründete Zieltechnologie (OpenAPI, Pydantic, asynchrone Audit-Jobs); eigene Versionierung und Authentifizierung, OAuth für Partneranbindungen erst bei Bedarf.
- **Metadata Store:** eigene MariaDB-Datenbank oder klar isoliertes eigenes Schema für Tenant, Mandate, Audit, Berechnungsregeln, Fallakte, Vergütungsereignisse, Invoicing und Revision; nicht in TonnEstate-Tabellen hineinschreiben.
- **Analytik:** DuckDB für importierte, versionierte Daten-Snapshots, Reconciliation und deterministische Rechenläufe; Append-/Snapshot-Logik und reproduzierbare Runs. DuckDB ist weder Nutzer-/Rechteverwaltung noch alleiniger Transaktionsspeicher.
- **Dokumentablage:** private, verschlüsselte Objektspeicherung mit Tenant-/Auftragszuordnung, Hashes, Aufbewahrungs- und Löschpolitik; niemals originale Kundendokumente in öffentlichen Repositories oder ungeprüften Modellprompts.
- **KI-Layer:** vorhandene lokale Ollama/Modelle oder verifizierte FruitStack-Modellports ausschließlich für Klassifikation, Regelvorschläge und Erklärung; Schema-Validierung plus Freigabestatus. Kein LLM bei der eigentlichen Betragsberechnung.
- **Workflow:** vorhandenes n8n oder ein existierender verifizierter FruitStack-Ausführungsadapter für Job-Orchestrierung; die Berechnung wird nicht in n8n-Nodes implementiert. Bei Integrationslücke zunächst einfacher Job-Runner mit klarer Schnittstelle statt neuer Plattform.
- **Provenienz:** unveränderliche Audit-Run-Identität, Eingangsdateihash, Parser-/Modell-/Regelversion, Ausgangsparameter, Änderungsprotokoll, Ergebnis- und Belegreferenzen.
- **Vertrieb:** StarFruitMe allenfalls als gesonderter, zulässiger Firmen-Discovery-Eingang; GreenGrapeMe später für qualifizierte Vermarktung, keine automatische ungefragte Kaltakquise.

**Zentrale Trennung:** Das FruitStack-Ökosystem darf Dienste bereitstellen, aber der produktbezogene Source of Truth für Verträge, Differenzen und Erfolgsabrechnungen liegt ausschließlich bei LowHangingFruitMe. Keine geplante Schnittstelle gilt allein aufgrund ihrer Existenz im anderen Repo als produktiv integriert.

## 5. Datenpipeline und Zustandsmodell

Upload/Connector -> Malware- und MIME-Prüfung -> unveränderlicher Upload-Snapshot -> Dokumentklassifizierung -> OCR/Text/Tabelle -> Vertragsklausel mit Fundstelle -> explizite Berechnungsregel in Validierung -> Datenimport und Mapping -> Supplier/SKU-Resolution -> Datenqualitäts-Gates -> deterministische Calculation Run -> Gutschriften/Verrechnungen-Reconciliation -> belegter Finding Case -> Freigabe -> Export -> Recovery-Meldung -> Rechnungsbasis.

**Minimalzustände:**
- Audit: CREATED -> WAITING_FOR_DATA -> READY_FOR_REVIEW -> CALCULATING -> REVIEW_REQUIRED/COMPLETE/FAILED.
- Vertragsregel: EXTRACTED -> NEEDS_CONFIRMATION -> APPROVED -> SUPERSEDED.
- Finding: DRAFT -> EVIDENCED -> CUSTOMER_RELEASED -> CUSTOMER_DISPUTED/CLOSED.
- Recovery: NONE -> CLAIMED_BY_CUSTOMER -> SUPPLIER_ACCEPTED/REJECTED -> REALIZED_PARTIAL/REALIZED_FULL -> REVERSED.
- Fee: NOT_BILLABLE -> ELIGIBLE -> INVOICED -> PAID -> ADJUSTED.

Transitions müssen autorisiert, atomar und idempotent sein. Reporting darf „identifiziert“, „vom Lieferanten bestätigt“, „verbucht“, „realisiert“ und „uns fakturiert“ nicht vermengen.

## 6. Ergebnisobjekt / Report

Je Finding: case_id, tenant_id, agreement_revision_id, legal_entity_id, supplier_id, period_start/end, rule_id, rule_version, contractual_scope, eligible_net_base, expected_rebate_net, recorded_rebate_net, calculated_variance_net, unsupported_amount_net (wenn offen), evidence_refs (Seite/Zelle/Transaktions-ID), missing_data, quality_status, reviewer_id, audit_run_hash, occurred_at. Kein einzelner Confidence-Wert ersetzt fehlende Rohdaten oder Vertragsklärung.

Der Report erhält Gesamtbasis, geprüfte und ungeprüfte Positionen, Ausnahmen, abgeglichene Gutschriften und getrennte, jeweils belegte Beträge. Die an den Lieferanten verwendbare Differenzaufstellung enthält nur den für die Sache erforderlichen Ausschnitt und wird vom Kunden selbst autorisiert.

## 7. ERP- und CRM-Distributionsstrategie

Ein allgemeiner CRM-Markt ist **kein** ausreichender Grund für einen Connector. Gesucht wird ein System, das vertragliche Einkaufs- und Lieferantendaten tatsächlich bereitstellen kann. Reihenfolge folgt Datenabdeckung und realer Nachfrage, nicht nur Größe des App-Marktplatzes:

**P0: Upload/API.** CSV/XLSX/PDF/XML ohne ERP-Abhängigkeit. Dadurch direkt nutzbar und echte Feldanforderungen messbar.

**P1: Lexware Office.** Offizielle REST/Public-API und Technologiepartnerprogramm mit Partnerverzeichnis. Schwerpunkt buchhalterische Belege, Gutschriften, Zahlungs-/Buchungsinformationen; nicht die artikelgenaue Warenwirtschaft ersetzen. Public API setzt laut Lexware einen entsprechenden Tarif voraus; weitere Partnerrechte nur nach Zusage.

**P1: weclapp.** Kaufmännisch plausibles Ziel aufgrund der integrierten Warenwirtschaft; API-Scope, Berechtigungen und vollständige Einkaufs-/Gutschriftendaten erst mit dokumentierten Testfällen bestätigen.

**P2: Odoo.** Relevanter Einkauf + Odoo Apps; dünnes installationsfähiges Modul mit Konfiguration, autorisierter Export-/Sync-Funktion, Fallanzeige und Deep Link ins Portal. Vorher Edition/API-Zugänglichkeit und Store-/Zahlungsregeln prüfen.

**P2: ERPNext/Frappe.** Frappe Cloud Marketplace fordert öffentlichen, GPL-kompatiblen Quellcode der **App**; deshalb Connector als eigenständiges offenes Integrationspaket, während die proprietäre Bonusengine über die API betrieben wird. Zulässigkeit externer Vergütung/Remote-Engine und Review müssen separat bestätigt werden.

**P2: Dolibarr.** DoliStore-Vertrieb und Lieferanten-/Einkaufsdaten prüfen; PHP-Modul ausschließlich als dünner Client. Lizenz der konkreten übernommenen Modulkomponenten beachten.

**P3: OroCommerce/OroCRM, JTL, Xentral, Business Central, DATEV.** Nur bei nachweislicher ICP-Nachfrage und dokumentierter Datenverfügbarkeit. OroCommerce für B2B-Kontext möglich, aber nicht automatisch Quelle vollständiger Einkaufsboni; reiner CRM-Connector wäre voraussichtlich schwach.

**Partner/Marktplatz ≠ Bezahlung:** Dort wird ein Connector gefunden; Kunde schließt den Prüfdienstvertrag grundsätzlich mit LowHangingFruitMe. Ob die Plattform externes Billing, Kostenlos-Connector-Modell oder Provisionen zulässt, ist eine eigenständige Freigabefrage. Keine Umgehung von App-Store-Richtlinien.

## 8. Kommerzieller Betriebsablauf

Vor Audit: Kunde bestätigt Leistungsumfang, eindeutig benannte Gesellschaft, Bonusperiode, bekannte/streitige Altansprüche, Berechtigung zum Datenzugriff und Nachweispflichten. Der Auftrag definiert die Vergütungsbasis und die Zuschreibung zu einzelnen Case-IDs.

Modellannahme: **3 % von der nachweislich zusätzlich und kausal aufgrund des Reports realisierten Nettovergütung**, ohne Umsatzsteuer, ohne bereits bekannte/abgerechnete Positionen, ohne Mehrfachzählung bei Zahlung und Gutschrift. Eine Gutschrift zählt nur, wenn sie den wirtschaftlichen Vorteil tatsächlich bewirkt (Zahlung/Verrechnung nach vereinbarter Definition). Teilrealisation proportional; Storno/Abweisung als Korrekturereignis. Automatisch nur Rechnungsvorschlag; finale Rechnungsfreigabe durch berechtigten Betreiber.

**Beispiel, keine Prognose:** Eindeutig nachgewiesene zusätzliche Gutschrift/Verrechnung von 24.000 EUR -> 2.400 EUR netto Erfolgshonorar; Rechnung und USt nach anzuwendenden gesetzlichen Vorschriften. Noch nicht realisierte rechnerische Differenz von 36.700 EUR -> 0 EUR abrechenbarer Erfolg.

Die gesetzlichen Grenzen bei Rechtsdienstleistung/Inkasso nach RDG sind vor Markteintritt mit einer qualifizierten Stelle zu prüfen. Rechtsauslegung für einzelne streitige Verträge, eigenständige Lieferantenverhandlungen und Fremdinkasso sind nicht durch das technische Konzept legitimiert.

## 9. Datenschutz, Sicherheit und Öffentlicher-Repo-Grenze

Public GitHub bedeutet: **keine Kundenbelege, extrahierten Vertragsinhalte, echten personenbezogenen Datensätze, Secrets, Tokens oder proprietären FruitStack-Komponenten**. Testdaten synthetisch oder ausdrücklich frei nutzbar. Alle Kundendaten getrennt vom Entwicklungsrepository.

Vorgaben: Mandantenisolierung in jeder Abfrage, default-deny, read-only ERP-Scopes, verschlüsselte Datenhaltung und TLS, Secret-Rotation, kurzlebige Downloadlinks, Sicherheitsprüfungen für Uploads inkl. ZIP-Bomben/aktive PDF-Inhalte, keine Ausführung von Office-Makros, Rate Limits, max. Datei-/Zeilenumfang, Audit Logging, Trennung von Rohbelegen und KI-Kontext, Datenminimalisierung, vertragliche Löschfristen sowie Backup-/Restore-Probe. AVV nach Art. 28 DSGVO soweit Rolle und Verarbeitung dies erfordern; keine pauschale Behauptung, alle Daten wären personenbezogen.

Prompt-Injection: hochgeladene Dokumente sind ausschließlich Daten, niemals ausführbare Anweisungen an Agenten. Externe Modell-APIs sind standardmäßig deaktiviert, bis Vertrags-/Datenprüfung und kundenseitige Freigabe vorliegen.

## 10. Messbare Produktqualität und Wirtschaftlichkeit

**Fachliche Messgrößen:** Import-Abdeckung je Datenbestand, Anteil gültiger Vertragsregeln, Anteil durch Quellen/Transaktionen vollständig belegter Fälle, Summe der ungeklärten Lücken, falsch positive Differenzen im manuell geprüften Goldstandard, Reproduzierbarkeit von Audit-Runs, Zuordnung von Recovery-Ereignissen.

**Ökonomische Messgrößen:** qualifizierte Prüfaufträge, geprüfte Einkaufsvolumina (nicht Umsatz des Produkts), nachgewiesene Differenzen, bestätigte und tatsächlich realisierte Beträge, abrechenbarer Anteil, fakturierte und bezahlte Gebühren, Zeit- und Infrastrukturkosten je Audit, Einspruchsquote, Wiederbeauftragungen. Ein Testlauf mit simulierten Fällen ist keine Kundenvalidierung.

**Go-/No-Go:** vor einer kostenpflichtigen Einführung mindestens ein sauber dokumentierter Pilot mit echten autorisierten Daten, reproduzierbarer Rechenregel, externer fachlicher Prüfung des Differenzfalls und tatsächlich belegter Realisierung bzw. begründetem Null-Ergebnis. Die Zahl der Pilotkunden, Zielmargen und eine Rückgewinnungsquote sind **offene Hypothesen**, nicht als Fakten gesetzt.

## 11. Etappierung

**M0 – Spezifikation:** Fachregeln R1 und R2; Datenvertragsmodell; Donor-Lizenzen; Sicherheits- und Vertragsabgrenzung; synthetischer Goldstandard.

**M1 – vertikaler, ausführbarer Upload-Audit:** geschützter Login, Upload, Parser, Datenmapping, deterministic R1 engine, Gutschriftenabgleich, Test-Report, API und Tests. Keine erfundenen Lieferanten-/Forderungswerte.

**M2 – Revenue Ledger:** Case-ID, Kundennachweis, Teilrealisierung/Storno, Erfolgszuordnung, Rechnungsvorschlag, Vorab- und Folgeabstimmung.

**M3 – erste API-Integration:** Lexware Office mit tatsächlichem Testkonto und belegtem Datenumfang; ein Warenwirtschaftsconnector erst nach M1-Abnahme.

**M4 – Marktplätze:** Partnerzulassung, Connector-Pakete, Veröffentlichung, Pilotkunden, wirtschaftliche Wirksamkeit. Der volle Marketingprozess bleibt außerhalb des Audit-Kerns.

Die genaue Reihenfolge der Integrationen wird erst nach Datenzugriffstests und kaufmännischer Nachfrage verifiziert, nicht aufgrund einer pauschalen „in fünf Tagen fertig“-Schätzung.

## 12. Quelle/Evidenz der Konzeptentscheidungen (Abruf 02.11.2026)

- https://www.distroagents.com/ – US-Vorbild, Anbieterangaben als Marketingangaben behandeln.
- https://revotail.com/rebate-management – deutscher Rebate-/Recovery-Wettbewerb, tatsächlicher Leistungsumfang vor Positionierung erneut abgleichen.
- https://developers.lexware.io/docs/ – Lexware-API, Endpunkte und Grenzen.
- https://www.lexware.de/partner/modelle/ – Lexware-Technologiepartner, Anforderungen/Marketing.
- https://docs.frappe.io/cloud/marketplace/publishing-an-app-to-marketplace – Frappe-Review und Open-Source-Pflicht.
- https://github.com/OCA/connector – OCA-Connector und Lizenzgrenzen.
- https://www.gesetze-im-internet.de/rdg/__2.html und https://www.gesetze-im-internet.de/rdg/__10.html – Rechtsdienstleistung/Inkasso.
- https://www.gesetze-im-internet.de/bgb/__195.html und https://www.gesetze-im-internet.de/bgb/__199.html – allgemeine Verjährung; individuelle Fristen/Vertragsabreden gesondert prüfen.
- https://eur-lex.europa.eu/eli/reg/2016/679/oj – Datenschutz-Grundverordnung.

Weitere normative Dokumente: [Donoren](DONORS.md), [API/Daten](API_AND_DATA.md), [Vertrag/Umsatz](LEGAL_AND_REVENUE.md), [Lieferplan](DELIVERY_PLAN.md).

**Grundsatz:** Keine Implementierungsbehauptung ohne Commit, Tests und – bei externen Integrationen – echte API-/Partnernachweise.
