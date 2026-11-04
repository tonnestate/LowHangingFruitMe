# LowHangingFruitMe – verbindliches fachliches und technisches Konzept (laufend konsolidiert)

**Stand:** 03.11.2026 | **Status:** v0.13 Staging-Implementierung, CI-synthetisch geprüft; kein produktiver Kundenbetrieb | **Produktverantwortung:** eigenständiges FruitStack-Schwesterprodukt

**Technischer Umsetzungsabgleich v0.13:** Die harten R2-Anwendungsarten sind jetzt als `tier_semantics` mit verifizierter Fundstelle im Parser und in den HMAC-Regelhash eingebunden. Mappingfreigaben sind im HTTP-Staging für beide Datensätze gesondert HMAC-signiert und registriert. Die Audit-Quoten werden aus den bereitgestellten Kontrollsummen abgeleitet und im Kundenbericht/Portal angezeigt; echte **wertgewichtete ERP-Quelldatenabdeckung** bleibt mangels belastbarem externen Nenner `null`. Die verbindlichen externen Pilot- und RDG-Gates bleiben ausdrücklich offen.

## Verbindliche Ergänzungen zur fachlichen Abnahme – 03.11.2026

Diese Ergänzungen gehören zum fachlichen Querschnitt des Produkts und sind bei jeder Implementierung, jedem Test sowie der vierwöchigen Pilotabnahme zu berücksichtigen. Die vollständige Umsetzung wird **nicht** allein durch diese Konzeptänderung behauptet.

### 1. R1 priorisieren, R2 früh hart sperren

R1 (einfacher Jahresbonus) bleibt der erste echte Umsatzfall. Bei R2 müssen **vor** einer finanziellen Berechnung die Semantik der Schwelle, die Bezugsbasis, der Zeitraum, der Staffelbeginn und alle Grenzwerte fachlich eindeutig dokumentiert sein. Die Ausprägungen sind **nicht austauschbar**:

- `RETROACTIVE_FULL_BASE`: erreichte Staffel gilt rückwirkend auf die gesamte anrechenbare Basis.
- `MARGINAL_PER_TIER`: Betrag wird getrennt je Umsatzscheibe beziehungsweise Band berechnet.
- `FIXED_THRESHOLD_REWARD`: feste, vertraglich vereinbarte Prämie ab der Schwelle.
- Nur oberhalb einer Schwelle geltende Einzel-Mehrbeträge dürfen nicht unter einer der beiden vorgenannten Prozentvarianten **angenommen** werden: falls die Vertragssemantik nicht exakt zu einem implementierten Regeltyp passt, **NEEDS_REVIEW / NOT_CALCULABLE** und **keine Geldzahl**.

Die explizite interne Typangabe ist nur technische Struktur; die zugrunde liegende Klausel muss vom berechtigten Vertragsprüfer **mit Originalfundstelle** bestätigt werden. Parser, Vorschlagsmodell und Testfälle dürfen eine fehlende Festlegung weder aus einem Prozentsatz noch aus einem negativen/positiven Betrag ableiten. Ein unbekannter `kind`, fehlende Staffelgrenzen, widersprüchliche Belege oder ein nicht bestätigter Wechsel der Staffel-Semantik verhindern die Freigabe. **Keine implizite Fallback-Staffel.**

### 2. Audit-Level-Qualität sichtbar und berechenbar

Kundenberichte zeigen neben den Finding-Details drei eigenständige, nachvollziehbar berechnete Kennzahlen mit Zähler, Nenner, Prüfstand und Fehlgründen:

| Kennzahl | Fachliche Definition | Nicht verwechselt mit |
|---|---|---|
| `data_coverage_pct` | Anzahl belegbar importierter Einkaufs-/Gutschriftenzeilen relativ zu den **separat gelieferten** ERP-Kontrollzeilen; `null`, wenn kein geeigneter Nenner vorliegt. Überdeckung wird separat als Widerspruch ausgewiesen, nicht als >100 % Leistung. | Echtem Beweis, dass das ERP alle historischen Buchungen enthält |
| `rule_clarity_pct` | Anteil der im Auftrag erwarteten Bonusregeln mit fachlich eindeutig zugeordneter, quellbelegter und aktiv freigegebener Berechnungssemantik; bei fehlendem Regelregister `null`, nicht pauschal 100 %. | KI-Confidence oder juristischer Anspruchssicherheit |
| `reconciliation_completeness_pct` | Anteil der erforderlichen, separat erhaltenen Kontrollpaare (Einkauf und Gutschrift), bei denen **Zeilenzahl und Nettobetrag** exakt übereinstimmen; `null`, wenn keine verwertbaren Kontrollen verfügbar sind. | Unabhängiger Buchhaltungsprüfung |

Für die jetzige Ein-Lieferant-/Ein-Vertrag-Engine können technische Werte aus dem vorhandenen Readiness-Resultat abgeleitet werden; bei fehlenden, mehrdeutigen oder nicht überprüfbaren Nennern **nicht raten**. Zusätzlich werden `readiness_status`, `issue_code`, `blocking_dataset` und konkrete Maßnahmen wie „ERP-Auszug für die komplette Vertragsperiode erneut exportieren“ angezeigt. `NEEDS_DATA` bezeichnet fehlende oder unzureichende Eingaben, `NEEDS_REVIEW` fachlich unklare Zuordnungen; `NOT_CALCULABLE` bedeutet eine die Berechnung ausschließende Unstimmigkeit. Eine Qualitätsquote kann **nie** einen BLOCKER oder fehlende HMAC-/Reviewer-Freigabe überstimmen.

### 3. Lexware Office P1: bewusst eng

Die erste Lexware-Integration ist ein **lesender Beleg- und Gutschriftenadapter für R1**: Lieferantenidentität, Belegkopf, vorhandene Rechnungs-/Gutschriftenpositionen, Nettobeträge, Datum, Buchungsstatus und nachweisbare Verknüpfungen. Zugriffsrechte, Edition/Tarif, API-Feldabdeckung und Pagination sind mit einem real autorisierten Testkonto zu belegen. **Keine** automatische Garantie artikelgenauer Warenwirtschaftspositionen, vollständiger Einkaufsstatistiken, Bankbestätigung oder unbeschränkter Historie. Wo die API Positionen nicht in der für R1 notwendigen Detailtiefe liefert, wird ein autorisierter CSV-/XLSX-Export eingefordert und der Datenstatus explizit eingeschränkt. Kein ERP-Writeback und kein paralleles Warenwirtschaftssystem.

### 4. Pilot-Abnahme: fest definierte Prüfschwelle

**Interne Pilot-Akzeptanzhypothese**, vor echter Kundenabnahme fachlich zu bestätigen:

- Ein kompletter zwölfmonatiger Vertragszeitraum; **mindestens 200.000 EUR dokumentiertes bonusfähiges Nettobezugsvolumen**, bezogen auf einen Lieferanten/eine rechtliche Einheit und eine nachweislich anwendbare R1-Vereinbarung. 200.000 EUR ist eine **gewählte Abnahmeschwelle**, keine statistisch hergeleitete Mindestgröße des Marktes.
- Auf der durch Datenimport kontrollierbaren Ebene mindestens **95 % wertgewichtete Abdeckung** der laut Kontrollbericht erwarteten anrechenbaren Einkaufsbasis und höchstens **10 % der relevanten Quellpositionen** mit `NEEDS_DATA` oder `NEEDS_REVIEW`. Für einen **finalen Differenzbetrag** müssen allerdings sämtliche die Bonusbasis beeinflussenden Lücken geklärt und **100 % Zeilenzahl-/Nettobetrag-Reconciliation** mit den vorliegenden Kontrollberichten erreicht sein. Ein nicht-finaler Teilreport ist kein erfolgreicher Geldbefund.
- Unabhängiger fachlicher Goldstandard durch **eine namentlich dokumentierte qualifizierte Einkaufs-/Controlling-Person, die nicht die Regel im System freigegeben und nicht die Programmierung durchgeführt hat**. Sie prüft Originalklausel, Periodenbasis, Retoure, Gutschrift, Endbetrag und Evidenzkette. Die Rollen-/Unabhängigkeitsgrenze wird protokolliert.
- Abnahme bei korrektem, unabhängig überprüftem Differenzbetrag **oder** plausibel belegtem Null-Ergebnis; **keine** künstliche Recovery erforderlich. Eine tatsächliche Realisierung darf nur mit echten Nachweisen beansprucht werden; eine Simulation ist dauerhaft als solche zu kennzeichnen.

Diese Schwellwerte sind produktinterne Pilot-Entscheidungen und keine behaupteten Leistungsdaten. Sie ersetzen weder eine Wirtschaftlichkeitsanalyse noch die Möglichkeit, einen kleineren Fall als **Testfall, nicht als erfüllte Pilot-Abnahme** zu prüfen.

### 5. RDG-/Erfolgshonorar-Prüfung als kommerzielles Startgate

**Vor dem ersten zahlenden Kunden** ist eine dokumentierte externe Prüfung durch einen in Rechtsdienstleistungs- und Vertragsrecht entsprechend spezialisierten Rechtsanwalt beziehungsweise eine qualifizierte externe Stelle erforderlich. Schriftlich klären: technische/kaufmännische Differenzakte versus rechtliche Anspruchsprüfung, kundeninterne Mitwirkung versus unsere Kommunikation mit Lieferanten, Zulässigkeit der konkreten 5-%-Erfolgsvergütung, erforderliche Vertrags-/AVV-/TOM-Bestandteile und Grenzen von Nachlauf/Provisionszuordnung. Ohne dokumentierte Freigabe: kein autonomes Forderungsschreiben, keine Lieferantenverhandlung, kein Inkasso und **keine kommerzielle Live-Freigabe**.

### Konzeptpflege als fester Release-Schritt

Jede fachliche Änderung an R1/R2, Readiness, Fee-Attribution oder ERP-Import benötigt im **gleichen PR/Commit-Zyklus** eine aktualisierte Entscheidung in `docs/CONCEPT.md`, passende Abnahmekriterien in `docs/FOUR_WEEK_ACCEPTANCE.md`, einen tatsächlichen CI-Nachweis in `EVIDENCE.md` und die Abgrenzung von **Implementiert / Getestet / Offen** in `docs/IMPLEMENTATION_STATUS.md`. Fehlende echte Pilotdaten und externe Rechtsprüfung bleiben als OFFEN stehen, bis extern bestätigt.

## 0. Auftrag, Ergebnis und harte Grenzen

LowHangingFruitMe findet aus Kundendaten bereits wirtschaftlich entstandene, aber nicht oder nicht vollständig gutgeschriebene Lieferantenboni und andere **vertraglich eindeutig berechenbare** Einkaufsvergütungen. Das Produkt liefert eine prüfbare Differenzakte und verfolgt nach Kundeneingabe oder autorisiertem Buchungsabgleich, ob daraus tatsächlich zusätzlicher wirtschaftlicher Nutzen wurde. Es berechnet ausschließlich anhand dokumentierter Vertragsregeln und belegter Transaktionen. Eine KI darf Klauseln erfassen, Abgleichsvorschläge liefern und begründen; die KI darf weder rechnerische Ansprüche erfinden noch rechtliche Forderungen verbindlich feststellen.

**Nicht im v0.1-Scope:** autonomes Inkasso, eigenständige Verhandlungen mit Lieferanten, Forderungskauf, Auszahlung/Entgegennahme von Lieferantengeldern, automatisches Verbuchen von Gutschriften, vollautomatische juristische Vertragsauslegung, allgemeine Rechnungsaudit- oder ERP-Plattform, ein weiteres zentrales FruitStack-Memory oder ein weiterer Agenten-Orchestrator.

**Wettbewerbshypothese:** Erfolgshonorar-Audits sind nicht neu; insbesondere revotail kommuniziert bereits Rebate-Recovery-Leistungen. Differenzierung kann deshalb nicht allein „keine Grundgebühr, 5 % Erfolg“ sein, sondern wäre ein überprüfbares, eingebettetes, selbst bedienbares Produkt mit revisionsfähiger Nachweiskette, wiederverwendbarer API und ERP-Distribution. Noch **nicht** durch zahlende Kunden belegt.

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

Modellannahme: **5 % von der nachweislich zusätzlich und kausal aufgrund des Reports realisierten Nettovergütung**, ohne Umsatzsteuer, ohne bereits bekannte/abgerechnete Positionen, ohne Mehrfachzählung bei Zahlung und Gutschrift. Eine Gutschrift zählt nur, wenn sie den wirtschaftlichen Vorteil tatsächlich bewirkt (Zahlung/Verrechnung nach vereinbarter Definition). Teilrealisation proportional; Storno/Abweisung als Korrekturereignis. Automatisch nur Rechnungsvorschlag; finale Rechnungsfreigabe durch berechtigten Betreiber.

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

## Ergänzung v0.14 – maßgebliche Vertragsregelrevision (in Entwicklung)

Die maßgebliche Bonushöhe darf nur aus der **aktuell verifizierten Vertragsregelrevision** berechnet werden. Pro Mandant/Gesellschaft/Vertrag/Regel-ID muss genau ein aktueller freigegebener Approval-Beleg existieren; eine neue HMAC-geprüfte und authentifiziert unterzeichnete Freigabe ersetzt die vorherige atomar. Die alte Regel erhält einen unveränderlichen SUPERSEDED-Nachweis und darf für **neue** Audits nicht wiederverwendet werden. Bereits abgeschlossene Audits bleiben unverändert mit ihrer Originalregel und Quellhash für die spätere Belegprüfung erhalten. Ein laufender Audit blockiert gleichzeitig eintreffende Supersession bis zum Abschluss seiner geschützten Berechnung. Revisionsidentität und Dokumenthash dürfen nicht aus KI-Ausgaben geraten werden. Beim Upgrade werden ältere Freigaben ohne Revisionsindex nicht stillschweigend als aktuell angenommen; erneute kontrollierte Bestätigung ist erforderlich.

Die vollständige Statuskette EXTRACTED → NEEDS_CONFIRMATION → APPROVED → SUPERSEDED/REVOKED (inklusive tatsächlicher Docling-Extraktion, Nachtragsketten, aktiver Benutzerführung und formaler Bestätigungsübergänge) ist mit dem derzeitigen Revisionskopf **noch nicht vollständig implementiert** und bleibt ein separates Abnahmekriterium innerhalb v0.14. 5 % bei neuen Recovery-Fällen bleiben unverändert nur eine Gebührenhypothese ohne Rechnungsfreigabe.


## v0.14-Härtung der parallelen Freigabevorgänge (04.11.2026)

Revoke, Supersede und Audit-Guard müssen sämtliche konkurrierenden Sperren in der festen Reihenfolge **Revisionskopf → Approval → Reviewer-Grant** nehmen. Das Revoke-Verfahren ermittelt die Lineage zunächst ohne Row-Lock, sperrt danach den zugehörigen Revisionskopf und erst anschließend Approval und Reviewer. Legacy-Freigaben ohne Lineage bleiben für neue Audits blockiert. Diese Änderung behebt die zuvor uneinheitliche Sperrreihenfolge, stellt aber keinen vollständigen Entwurfs-/Nachtrags-Lifecycle und keinen produktiven Migrationsnachweis dar.


### Kontrolliertes Datenbank-Rollout (04.11.2026)

Migrationen werden ausschließlich als expliziter, autorisierter Wartungsvorgang ausgeführt. Die eigentliche API führt keine DDL aus. Ein MariaDB-Advisory-Lock schützt parallele Installer, jede bekannte Migration wird mit SHA-256 und einem vor Ausführung persistierten IN_PROGRESS-Marker registriert, ein partiell angewendetes DDL blockiert weitere Automatik. Altbestände ohne signierte Migrationshistorie werden weder stillschweigend übernommen noch rückwirkend neu bewertet. Für reale Altbestände bleiben Backup-/Restore-Probe, Schema-Reconciliation und kontrolliertes Go/No-Go verpflichtend.


## v0.14 – EXTRACTED bis APPROVED im realen Auditpfad (Implementierung, CI folgt)

Ein mandanten- und gesellschaftsgebundener Vertragskandidat wird aus der bereits ClamAV-geprüften Vertrags-PDF unter exakter SHA-256-Bindung erzeugt (`EXTRACTED`). Der separate authentifizierte Prüferprozess legt nur die tatsächlich vom Parser gelisteten dokumentinternen `evidence_ref`-Fundstellen zur expliziten Bestätigung vor (`NEEDS_CONFIRMATION`). Ein Freitextbeleg, ein LLM-Entwurf oder ein `approved=true` ohne den aktuellen Kandidaten darf den signierten Bundle-Pfad nicht mehr erreichen. `ApprovalRegistry.register` revalidiert Dokumentdigest, Regelhash, Prüfer, Dokumentrevision und Vertrags-/Regelrevision innerhalb derselben Transaktion, die den aktuellen Regelkopf setzt, und schreibt das Kandidatenereignis `APPROVED`. `SUPERSEDED`/`REVOKED` folgen unter derselben Revisionssperre; Alt-Audits bleiben historisch lesbar. Alte direkte Signiervorgänge sind nur im ausdrücklich isolierten Testpfad aktiv.

Der Einstieg ist absichtlich nur PDF; DOCX wird nicht ohne Extraktionsbenchmark als gleichwertige Vertragsquelle ausgegeben. Docling arbeitet im ressourcenbegrenzten Subprozess, nicht mehr im Webprozess, doch ein separater OS-/Firewall-Sandboxnachweis und echte Vertragsprüfung fehlen weiterhin. Keine automatische Feststellung eines Anspruchs oder rechtsgeschäftliche Unterschrift.


## Sicherheitsgate für die Vertrags-PDF-Extraktion (04.11.2026)

Der Parser wird nur über einen root-kontrollierten Sandbox-Launcher gestartet; der Worker prüft die tatsächliche Netzwerk-Namespace-Differenz und die ausschließliche Sichtbarkeit des Loopback-Interfaces. Die Operatorbereitschaft benötigt einen aktiven Sandbox-Preflight; eine ungeprüfte Subprozesskonfiguration genügt nicht. Elternprozess-seitige harte Ausgabelimits und gezieltes Töten der Prozessgruppe ergänzen die Worker-Ressourcenlimits. Fehlende Isolation führt zu keiner Klausel-Extraktion und keiner signierten Vertragsfreigabe. Der fachliche Goldstandard, echte Docling-PDF-Benchmarks und die vollständige OS-Isolationsabnahme bleiben externe Go-Live-Gates.
