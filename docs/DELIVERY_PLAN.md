# LowHangingFruitMe – Umsetzung, Testabnahme und Markteintritt v0.1

**Stand:** 03.11.2026 | **Ist:** ausführbarer Python-Kern v0.9, importfähige Datenadapter, abgesicherte Audit-API und private, scannerpflichtige Upload-Staging-API sowie Marketing-Website 0.1.0; **keine realen Kunden- oder Produktionsabnahmetests**. Dieser Plan setzt Prioritäten, aber behauptet keine feste Laufzeit, produktive Anbindung oder Marktvalidierung.

## Ergänzende verbindliche Prüfgates (03.11.2026)

**R2 vor Berechnung:** Parser muss unklare rückwirkende, Überschuss- oder scheibenbezogene Staffelsemantik sofort als `NEEDS_REVIEW` kennzeichnen. Aus unklaren Vorschlägen entstehen weder genehmigungsfähige Regeln noch Geldbefunde; die übermittelte eindeutige Staffelklasse muss mit belegter Vertragsfundstelle und Reviewer-Freigabe verknüpft werden.

**Audit-Level-Datenqualität:** `data_coverage_pct`, `rule_clarity_pct`, `reconciliation_completeness_pct` nach `CONCEPT.md` definieren, pro Audit begründen und mit fehlenden Nennern korrekt als `null` ausgeben. Zusätzlich maschinenlesbare blocker/warning- und `NEEDS_DATA`-/`NEEDS_REVIEW`-Gründe. **Qualitätskennzahlen nicht als Vollständigkeitsattest missverstehen.**

**Lexware P1:** Read-only R1-Rechnungs- und Gutschriftenbelege sowie benötigte Header/Positionsfelder. Kein vollständiger Warenwirtschaftsnachbau; fehlende historische/positionsbezogene Einkaufsdaten per Export und explizitem Data-Readiness-Gate nachfordern. Echte Testkonto-Abnahme vor „integriert“.

**Realer R1-Pilot:** volle zwölf Monate, mindestens **200.000 EUR** kontrolliertes bonusfähiges Nettovolumen (gewählte Pilot-Schwelle, nicht Marktstandard), importbezogene Mindestabdeckung **95 % wertgewichtet**, ungelöste fachliche Positionen höchstens **10 %**, und vor **finalem** Finding vollständiger Reconciliation-Abgleich. Namentlich unabhängiger externer Einkäufer/Controller erstellt manuelle Goldstandard-Rechnung und zeichnet Quellenbefund sowie Nullfall oder echte, belegte Realisierung ab.

**Kommerzieller Go/No-Go:** Externe fachjuristische schriftliche RDG-/Erfolgshonorar-Abgrenzung, insbesondere keine eigenständige Anspruchsdurchsetzung. Offene Rechts- und Datenschutzprüfungen sind harte Launch-Blocker, nicht nachträgliche TODOs.

**Pflicht-Dokumentationszyklus:** Bei jedem fachlichen Release `CONCEPT.md`, `FOUR_WEEK_ACCEPTANCE.md`, `IMPLEMENTATION_STATUS.md` und `EVIDENCE.md` synchron mit Nachweisen aktualisieren. Keine Pilot-/Release-Abnahme allein wegen grünem synthetischem CI.

## 1. Entwicklungsprinzip und Schutz gegen Scope-Drift

Ein vertikaler, voll belegbarer Pfad ist wichtiger als zehn unfertige Connectoren. Die fachliche Definition von **„Geld gefunden“** ist verschieden von **„Geld beim Kunden realisiert“** und **„unsere Rechnung bezahlt“**. Jede dieser Stufen bekommt eigene Messwerte und Abnahmetests.

Fehlende Daten und offene Rechtsfragen werden als konkrete Einschränkung im Ergebnis markiert. Ein Code-Agent darf weder neue Plattformen noch zusätzliche Datenbanken/Orchestratoren erfinden oder Umsatzprognosen als Nachweis ausgeben.

Für Architekturänderungen: reale bestehende FruitStack-Ports prüfen, Minimaladapter wählen, tatsächliche Integration gegen die Spezifikation testen. Keine ungefragten systemübergreifenden Codekopien. Die Produktquelle bleibt unabhängig.

## 2. P0 – Forschungs-/Entscheidungsarbeit vor der Implementierung

**P0.1 Fachlichkeit:** 1–2 anonymisierte **oder** rechtmäßig bereitgestellte echte Bonusvereinbarungen mit vollständigen periodischen Transaktions-/Gutschriftenbeständen als Goldstandard beschaffen. Prüfen: welches Datum ist Berechnungsanker, welche Werte sind bonifizierbar, wie funktionieren Nachträge, welche Zeilen sind offen, gibt es Nullfall-Daten? Solange kein Pilot vorhanden ist, synthetische Testfälle nutzen, aber keine echte Business-Performance behaupten.

**P0.2 Donor-Gate:** Docling, invoice2data, Frictionless, RapidFuzz gegen ausgewählte synthetische Dokumente/Tabellen in isolierter Umgebung testen. Version/Lizenz/Transitive Dependencies, Herkunft, Ausführungssicherheit und reale Ressourcen aufnehmen. P0-Scope ist klein, nicht alle Donoren gleichzeitig deployen.

**P0.3 Recht:** RDG-Abgrenzung, Erfolgshonorar und Daten-/Geheimnisschutz vor dem kommerziellen Launch zur Prüfung geben; erforderliche Änderungen in den Leistungsumfang zurückschreiben, nicht als vage Ausrede für ausbleibende Entwicklung verwenden.

**P0.4 Architekturanschluss:** MariaDB-/DuckDB-/Ollama-/n8n-Ports und Tenant-Isolation gegenüber tatsächlich laufendem FruitStack prüfen. Bei ungeprüftem Port mit einer expliziten isolierten Schnittstelle weiterentwickeln und später integrieren.

### P0-Fertigstellung

- Vertragsregel R1 anhand eines manuell belegten Goldstandards eindeutig.
- Genaue Importformate und benötigte Felder dokumentiert.
- Donor-Entscheidung für P0-Komponenten mit getesteten Artefakten und Lizenz.
- Sicherheits-/Datenarchitektur und Rechnungserfolg begrifflich abgegrenzt.

## 3. P1 – ausführbarer vertikaler Upload-Audit

**Lieferobjekte:** eigene API-/App-Struktur, Auth und Mandanten, sichere Dateiannahme, Docling-Adapter, tabellarische Importe und Frictionless-Prüfung, Vertragsregel als versioniertes Objekt mit manuellem Approval, deterministische R1-Rechnung, Gutschriftenabgleich, Case-Evidenz, JSON/PDF/XLSX-Export, Regressionstests.

**Akzeptanz:** synthetischer Bonusfall mit 200.000,00 EUR Nettobasis und 2 % Bonus ergibt exakt 4.000,00 EUR; schon gebuchte 1.500,00 EUR ergeben 2.500,00 EUR **rechnerische** Differenz. Tabellenfehler, Nullwerte, ungeklärte Lieferanten, Dokumentnachträge und Datenlücken melden EXCEPTION statt zu raten. Zweimal dieselben Daten ergibt gleiches berechnetes Ergebnis.

**Technisches Ziel:** API ist Headless und Portal nutzt dieselben Endpunkte. Keine separate Berechnungslogik im Web-Frontend, Odoo-Modul oder n8n.

## 4. P2 – Recovery- und Rechnungsledger

**Lieferobjekte:** unveränderliche Case-IDs, supplier accepted/declined, manual/uploaded recovery proof, read-only Settlement-Matching, Teilrealisierung, Storno, Gebührenzuordnung, Rechnungsvorschlagsfreigabe und Zahlungseingangsstatus.

**Akzeptanz:** 
- 2.500,00 EUR berechnete Differenz, davon 1.000,00 EUR realisiert -> 50,00 EUR netto Honorarvorschlag bei 5 %, nicht 125,00 EUR.
- Ein doppelter Payment-/Credit-Event erzeugt keinen zweiten Anspruch.
- Storno 300,00 EUR reduziert die realisierte Basis um 300,00 EUR und senkt den Honorarvorschlag um 15,00 EUR; keine automatisch abrechenbare Gebuehr. 
- Bei unklarer Zuordnung: DISPUTED; keine automatisch freigegebene Rechnung.
- Keine Lieferantenzahlung geht über unsere Konten.

## 5. P3 – eigener Kundenbereich und Verträge

**Lieferobjekte:** Landingpage, verständlicher Angebots- und Belegbedarf, Unternehmens-Account, Rollen, Vertragsannahme mit Versions-/Beweisbindung, Upload-/Mapping-Wizard ohne unnötige UI-Komplexität, Auditfortschritt, Findings-Liste, Berichtdownload, Ledger-Status und Supportkontakt.

**Abnahme:** Vertragstext und Gebührenbasis wurden **vor** Report-Freigabe eindeutig angenommen. Fremder Tenant kann auch bei direktem Link keine Daten sehen. E-Mail-Verifikation und Rollen gelten sowohl in Portal als auch API. Downloadlinks laufen ab. Kunden können eine Datenlöschanfrage veranlassen, deren gesetzliche Ausnahmen dokumentiert sind.

## 6. P4 – erste ERP-Integration

**Lexware Office:**
- offizielles Testkonto, minimale Rechte und API-Key-Handling/Partner-API-Freigabe;
- Beleg-/Kontakt-/Credit-Umfang protokollieren; die Public API ist laut offizieller Beschreibung ab einem passenden Lexware-Office-Tarif verfügbar;
- artikelgenaue Einkaufsdaten werden nicht vorausgesetzt, fehlende Artikel-/Warengruppendaten per Upload erheben;
- Read-only-Import und Widerruf testen, keine automatischen Buchungen.
- nach erfolgreichem technischen und fachlichen Test Bewerbung/Review als Technologiepartner.

**weclapp:**
- erst nach tatsächlicher API- und Berechtigungsklärung; Einkaufsgeschäftsvorfälle, Produkte, Lieferanten und Supplier Credits auf dokumentierte Vollständigkeit prüfen;
- bei unzureichender API-Abdeckung zusätzlich offiziellen CSV-/XLSX-Export anbieten, kein Screen Scraping.

**Odoo, ERPNext/Frappe, Dolibarr:**
- je ein **eigenständiges, dünnes** Modul: Setup, Tenant-/Service-Bindung, consentierte Datensynchronisation, Sync-Status, Deep-Link in das LowHangingFruitMe-Portal und ggf. Ergebnisanzeige;
- keine Kopie des Kernsystems in das Modul;
- keine nicht freigegebene Verkaufs- oder Billingumgehung; GPL-/AGPL-/MIT-konform pro Modul;
- Version/Edition/Marktplatztest und zulässige API-Berechtigungen dokumentieren.

**Später:** OroCommerce, JTL, Xentral, Business Central, DATEV nur nach Nachfrage oder belegten Kern-Datenlücken. Ein CRM ohne Einkaufs-/Settlement-Daten ist kein P1-Connector.

## 7. Integrationsverzeichnis mit harten Nachweisen

Für jede Anbindung ein Eintrag:
- Plattform, Version, Edition/Tarif, konkrete dokumentierte API-Berechtigungen, Auth-Flow;
- geprüfte Felder pro Entität (Supplier, Purchase, Invoice, Invoice Line, Credit Note, Settlement, Return);
- Ausfallverhalten, Limits, Pagination, historische Vollständigkeit, inkrementelle Sync-Kennzeichen;
- App-Store-Lizenz und Zulässigkeit externen Billing;
- veröffentlichte Plugin-Version, Testnachweise, Datenspeicher- und Löschverhalten;
- Testkonto und Integrationstest, getrennt von simuliertem Mock-Erfolg.

**Echte API-Abnahme erst bei realem Endpunkt-Call** und nachgewiesenem Datenumfang. Ein SDK oder ein Partnerlogo allein gilt nicht als Integration.

## 8. Qualitäts-, Security- und Operations-Gates

**Unit:** Decimal-/Rundung, Schwellenvarianten, Vertragsdatums-Überlappung, Duplikat/Storno, Teilrealisation und Fee-Attribution.

**Integration:** Parser gegen gescannte und textbasierte Vertrags-PDFs, validierte Tabellenimporte, Schemaänderungen, API-Auth, Upload-Sandbox, MariaDB/DuckDB-Snapshot, Reports mit Evidenz.

**E2E:** Unternehmen anlegen, Vertrag annehmen, Daten hochladen, Regel bestätigen, Audit starten, Ergebnis prüfen, Gutschrift buchen, Honorarvorschlag freigeben, Rechnung ausgeben und Zahlungseingang auswerten. Tests zunächst mit synthetischen Daten, realer Pilot **gesondert**.

**Security:** Cross-Tenant-IDOR, manipulierte Downloads, ZIP-Bomben, PDF-Missbrauch, Prompt Injection, Token-Leak, Rechteentzug, Datenlöschung, Replay/Webhook-Deduplikation, Backup-/Restore-Test und Ausfallverhalten.

**Proof-Rule:** für jeden abgeschlossenen Meilenstein Commit/PR, Testbefehle, tatsächliche Testresultate, Einschränkungen und offene Risiken protokollieren. Grün ohne tatsächliche End-to-End-Abnahme heißt lediglich Teilabnahme.

## 9. Minimale Repo-Struktur – Architekturziel, nicht schon vorhanden

- README.md
- docs/CONCEPT.md
- docs/DONORS.md
- docs/API_AND_DATA.md
- docs/LEGAL_AND_REVENUE.md
- docs/DELIVERY_PLAN.md
- docs/DECISIONS/ (nur für echte Donor-/Schnittstellenentscheidungen)
- app/api/ (API-Transport, Auth, Tenant-/Role Guards)
- app/domain/ (Approved Rules, Calculation, Reconciliation, Fee-Allocation)
- app/adapters/ (Docling, invoice2data, CSV, spezifische ERP-Connectors)
- app/storage/ (MariaDB / DuckDB / gesicherte Objektreferenzen)
- app/reporting/ (PDF/XLSX/JSON)
- portal/ (Web-Frontend)
- tests/fixtures/ (nur künstliche, rechtlich freie Datensätze)
- tests/unit/, tests/integration/, tests/e2e/
- integrations/ (erst mit konkreter Marktplatz-/Versionszulassung)

Kein vorgeschlagener Ordner gilt als vorhandene Implementierung.

## 10. Wirtschaftliche Go-/No-Go-Logik

Der Kunde zahlt nur nach belegtem wirtschaftlichem Erfolg. Damit trägt LowHangingFruitMe zunächst die Datenverarbeitungs- und Prüfungskosten. Für jeden Audit daher messen:

- processing_cost (Parser/Compute/Modell), human_review_cost, support_cost, onboarding_cost, marketplace_acquisition_cost;
- confirmed_realization_net, eligible_fee_net, billed_fee_net, received_cash_net;
- contribution_margin = received_fee_net minus variable Kosten, zeitlich periodengerecht zuordnen;
- net_recouped_per_case, days_to_realization, unpaid_customer_invoices, reversals.

Beispiel mit Variablen, **nicht** als validierte Markterwartung: Bei 5 % Gebühr und 150 EUR gesamten variablen Kosten ist der rein variable Break-even pro Audit bei mindestens 3.000 EUR belegter Realisierung, sofern keine weiteren Gebühren oder Rückstellungen anfallen. Bei Nullrecovery entstehen trotz 0 EUR Honorar weiterhin Kosten. Deshalb Pilotkundenselektion und begrenzte Audit-Ressourcen statt massenhafter ungesteuerter Gratisprüfungen.

**Kundenvalidierung:** mit eindeutig belegten Daten unterscheiden, wie viele Audits tatsächliche Berechnung, akzeptierte Differenzen, Geldzufluss und Zahlungen an uns erzeugen. Keine pauschalen 1–3-%-Ansprüche aus US-Marketing übernehmen.

## 11. Agentenauftrag für Umsetzung (nach Konzeptbaseline)

- Erst Repo-, Branch- und Dateistand lesen. Keine Änderung außerhalb des expliziten Workstreams.
- P0-/P1-Tests als falsifizierbare Fälle aus API_AND_DATA übernehmen. Kein Code, der Tests nur synthetisch „grün“ malt, aber die tatsächliche API nicht abdeckt.
- Donor nur bei nachgewiesenem Minimalnutzen, kommerziell nutzbarer Lizenz und Security-Abnahme einführen; Herkunft und genaue Version dokumentieren.
- End-to-End ohne fremde Daten und ohne Cloudzugriffe durchführen, solange Credentials/Einwilligung nicht existieren.
- In GitHub klare Diffs, Dokumentation des realen Status und konkrete Restaufgaben hinterlassen.
- Danach zielgerichtete ERP-Integration mit Testkonto und Partnervertrag; keine pauschalen „fertig“-Claims.

## 12. Erfolgskriterium des ersten Releases

Eine berechtigte Firma kann ihren Prüfvertrag annehmen, vollständige Daten hochladen, eine belegte und manuell genehmigte Bonusregel prüfen lassen, ein revisionsfähiges Ergebnis herunterladen und danach eine echte realisierte Gutschrift einem Case zuordnen. Der Betreiber kann daraus ohne Doppelerfassung eine korrekte Honorarrechnung erstellen. **Das ist das erste verkaufbare Produkt.**

Kein Kunde, kein echtes ERP-Login, keine validierte Forderungsrealisierung und keine Rechnungszahlung werden bereits durch diese Dokumentation behauptet.
