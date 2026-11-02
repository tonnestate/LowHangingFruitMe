# LowHangingFruitMe – GitHub-Donorenregister und Integrationsentscheidung v0.1

**Stand:** 02.11.2026. Quelle: GitHub-Repositorien/README/Lizenzdateien und offizielle Projektdokumentation. Eintrag **RESEARCHED** bedeutet identifizierte/verifizierte Existenz und dokumentierte Fähigkeiten, **nicht** durch LowHangingFruitMe ausgeführten, lizenzierten oder integrierten Code. Keine Übernahme ohne pin, Quellprüfung, SBOM und Reproduktionstests.

## 1. Übernahmekonzept

Der fachliche Kern (Bonusregeln, Verjährungs-/Datenwarnungen, Evidenzkette, Recovery-Ledger und Erfolgszuordnung) ist **eigene Produktlogik**. Donoren liefern ausgereifte Parser, Datenvalidierer, Fuzzy-Matcher und optional ERP-Integrationsmuster. **Keinen fremden kompletten SaaS-Stack in unser Produkt importieren.**

Vier Donor-Typen:
- **D1 – als Library:** permissive Lizenz, gezielte Installation mit festem Release, nur benötigte Funktionen; Urheberhinweise behalten.
- **D2 – als isolierter Prozess:** klar definierte Ein-/Ausgabe, minimale Berechtigungen und Datenweitergabe; Lizenz- und Sicherheitsprüfung weiterhin nötig.
- **D3 – Architektur/API-Referenz:** Quellcode nicht kopieren; offizielle dokumentierte APIs und Datenmodelle verwenden.
- **D4 – zurückgestellt/ausgeschlossen:** unnötiger Stack, unpassende Lizenz, fehlende Reife/fehlender Zweck.

Kompatibilität mit einem proprietären kommerziellen SaaS ist **nicht automatisch** durch GPL-/AGPL-Projektzugriff gegeben. Copyleft-, Hosting- und Netzwerkpflichten sind fallabhängig. Modul- und Abhängigkeitslizenzen müssen separat bewertet werden.

## 2. Konkrete externe Donoren

| ID / Priorität | Repository | Lizenz, verifiziert aus Projektquelle | Verwendung / exakte Grenze | Integrationsmodus |
|---|---|---|---|---|
| D01 P0 | [docling-project/docling](https://github.com/docling-project/docling) | MIT (LICENSE); Modelle mit ggf. eigenen Lizenzen | PDF-/Office-Layout, Tabellen, Fundstellen und OCR-Ausgabe; generischer Dokument-Adapter. Keine Bonusregeln und kein juristischer Vertragsentscheider. | D1 zunächst lokaler Python-Adapter |
| D02 P0 | [invoice-x/invoice2data](https://github.com/invoice-x/invoice2data) | MIT (LICENSE.md) | Templates zur Extraktion von Rechnungsnummer, Lieferant, Datum, Beträgen und bei passenden Layouts Zeilen. Originalbeleg/ERP bleibt Referenz. | D1 optionale Beleg-Pipeline |
| D03 P0 | [frictionlessdata/frictionless-py](https://github.com/frictionlessdata/frictionless-py) | MIT (LICENSE.md) | Eingehende CSV/XLSX-Datensätze gegen versionierte Tabellenschemas prüfen: Pflichtfelder, Datums- und Zahlentypen, unerlaubte Nulls, fehlerhafte Zeilen. | D1 Datenqualitäts-Gate |
| D04 P0 | [rapidfuzz/RapidFuzz](https://github.com/rapidfuzz/RapidFuzz) | MIT (README/LICENSE) | Vorschläge zur Zuordnung uneinheitlicher Lieferantennamen/Artikeltexte. Niemals automatisches Mergen ohne verifizierte Identität. | D1 Kandidatengenerierung |
| D05 P1 | [camelot-dev/camelot](https://github.com/camelot-dev/camelot) | MIT (README) | Ergänzung zur PDF-Tabellenextraktion, wenn Docling auf bestimmten Tabellen versagt. Kein Standardparsing aller PDFs doppelt. | D1 gezielter Fallback |
| D06 P1 | [opendataloader-project/opendataloader-pdf](https://github.com/opendataloader-project/opendataloader-pdf) | Apache-2.0 ab v2.0, frühere Versionen MPL-2.0 laut Projekt | Alternativer Parser für komplexe tabellarische PDFs; Version vor Einsatz pinnen und ggf. OCR-/Hybrid-Aufwand separat messen. | D2 Benchmark/Fallback, nicht parallel dauerhaft |
| D07 P1 | [dedupeio/dedupe](https://github.com/dedupeio/dedupe) | MIT | Optional trainierte Entity Resolution nach einem ersten manuell geprüften Korpus. Nicht nötig für einen ersten Lieferantenpilot. | D1 später, nicht MVP |
| D08 P0 | [fastapi/fastapi](https://github.com/fastapi/fastapi) | MIT | HTTP-/OpenAPI-Boundary und Upload-/Audit-Endpunkte. Kein fertiger Kundenzugriff, Auth/Rate Limit und Tenant-Grenze bleiben zu bauen. | D1 Web-Service-Framework |
| D09 P0 | [pydantic/pydantic](https://github.com/pydantic/pydantic) | MIT | Strikte Ein-/Ausgabe- und Vertragsregel-Schemas; Schemaänderungen versionieren. | D1 Schema-/Validierungslibrary |
| D10 P1 | [py-pdf/pypdf](https://github.com/py-pdf/pypdf) | BSD-3-Clause (LICENSE) | PDF-Seitenselektion, Metadaten und dokumentierte PDF-Manipulation; keine OCR-/Tabellenlösung. | D1 Hilfsbibliothek |

**Wichtig:** Donoren sind kein Ersatz für eine sichere Upload-Kette. Virenprüfung, MIME-/Magic-Byte-Prüfung, Office-Makroschutz, PDF-Missbrauchsschutz, ZIP-Bomben-Grenzen und Ressourcenlimits sind eigene Security-Controls; Parser werden mit isolierten Rechten ausgeführt.

## 3. ERP-, CRM- und Billing-Projekte: Donor ≠ Vollübernahme

| System | Repository / Quelle | Lizenz-/Produktgrenze | Nutzung |
|---|---|---|---|
| Odoo | [odoo/odoo](https://github.com/odoo/odoo) | Odoo-Edition/Module unterscheiden; OCA-Addons können AGPL sein | D3: offizielle Datenmodelle und Schnittstellen verstehen. Eigenes kleines Connector-Modul nur nach Markt-/Lizenzprüfung |
| Odoo OCA Connector | [OCA/connector](https://github.com/OCA/connector) | Repo AGPL-3.0; Module-Lizenzen einzeln | D3: Patterns für Jobs/Sync; kein Copy-Paste in proprietäre Bonusengine |
| Odoo Purchase Workflow | [OCA/purchase-workflow](https://github.com/OCA/purchase-workflow) | Repo AGPL-3.0 und Modul-Lizenzen | D3: Referenz für Einkäufe/Supplier-IDs; keine Kopie in SaaS-Kern |
| ERPNext | [frappe/erpnext](https://github.com/frappe/erpnext) | GPL-kompatibler App-Ökosystemkontext | D3: strukturierte Supplier-/Purchase-/Invoice-Mappings. Open-Source-App separat veröffentlichen, Backend bleibt über dokumentierte API |
| Frappe Marketplace | [frappe/marketplace](https://github.com/frappe/marketplace) | Marktplatz-Registry/Validierungsverfahren, nicht unsere Kernlizenz | D3: Publish-Verfahren als Referenz; cloud-spezifische Bedingungen beachten |
| Dolibarr | [Dolibarr/dolibarr](https://github.com/Dolibarr/dolibarr) | GPL-3.0 laut GitHub; Modul-Lizenzen verifizieren | D3: offizielle REST-/Modulkonventionen; dünner externer API-Client |
| Oro | [oroinc/platform](https://github.com/oroinc/platform) | konkrete Lizenz-/Plugin- und kommerzielle Nutzungsbedingungen vor Beginn prüfen | D3: potenzielles B2B-Distributionsziel, keine Priorität ohne Datenbedarfsnachweis |
| Documenso | [documenso/documenso](https://github.com/documenso/documenso) | AGPL-3.0 plus ggf. Enterprise-Funktionen; PostgreSQL-Betrieb | D4 im MVP. Nicht wegen bloßer Vertragsannahme separate Signaturplattform mit neuem Datenbankstack |
| DocuSeal | [docusealco/docuseal](https://github.com/docusealco/docuseal) | AGPLv3 + zusätzliche Bedingungen nach Projekt | D4 im MVP. Spätere Integration als isolierter Drittservice nur nach rechtlicher Prüfung |
| Lago | [getlago/lago](https://github.com/getlago/lago) | AGPLv3; umfangreiche Billing-Plattform | D4. Unverhältnismäßig für v0.1-Erfolgshonorar; eigenes kleines Ledger + bestehende Rechnungsstellung bevorzugt |
| Paperless-ngx | [paperless-ngx/paperless-ngx](https://github.com/paperless-ngx/paperless-ngx) | GPL-3.0 | D4. Kein vollständiges Dokumentenverwaltungssystem als Abhängigkeit erforderlich |
| PyMuPDF | [pymupdf/PyMuPDF](https://github.com/pymupdf/PyMuPDF) | AGPL-3.0 oder kommerzielle Lizenz, laut Betreiber | D4 ohne gesonderte Lizenz. Keine versehentliche indirekte Abhängigkeit im proprietären Produkt |

**Präzisierung:** Die bloße Nutzung eines offiziell dokumentierten Remote-API-Endpunkts ist etwas anderes als das Kopieren/Linken von Copyleft-Code. Trotzdem sind die jeweiligen Marktplatz- und App-Lizenzen gesondert einzuhalten.

## 4. Vorhandene FruitStack-Komponenten – begrenzter Wiederverwendungsauftrag

Die folgenden Aussagen stammen aus den am 02.11.2026 tatsächlich gelesenen Repository-READMEs; **nicht** aus einem ausgeführten gemeinsamen End-to-End-Test.

| Komponente | Aus README belegter Zweck | Beitrag zu LowHangingFruitMe | Übernahmegrenze |
|---|---|---|---|
| MangoMe | persistenter governter Arbeitszustand/Evidenz; experimenteller Entwicklungsstand | optionales Evidence-/Run-Handoff, **nicht** Ersatz für das kaufmännische Recovery-Ledger | nur verifizierte Port-Schnittstelle; keine zweite Truth-Authority |
| BlueberryMe | sensible Daten maskieren und zweckgebundene Offenlegung; experimenteller Referenzstatus | mögliche Privacy-Policy-Boundary für Agentenkontext | produktive Isolation weiter eigenständig erzwingen; keine DSGVO-Konformität durch README behaupten |
| PomeloMe | deterministische agentische Ausführung mit Effekt-Reconciliation | optional für genehmigte externe Jobs/Notifications | kein Muss im MVP; kein zweites Workflow-Kernel bauen |
| StarFruitMe | NACE-/Unternehmens-Discovery mit DuckDB/MCP, aber kein verifizierter vollständiger Google-Live-Betrieb | später ICP-Recherche über erlaubte Quellen | niemals Quelle für Bonustransaktionen oder Finanzdaten |
| GreenGrapeMe | strategischer B2B-Sales-Prozess, derzeit P0/kein Deployment | mögliche spätere Vertriebserweiterung | nicht Teil der Audit-Pipeline, nicht als live behaupten |
| KIGOR | dokumentierte Beleg-/Fundstellen- und Dublettenmuster, eigenständiges internes Projekt | nur konzeptionelle Muster zu Quellen, Unsicherheit und human review | private Implementierung nicht in öffentliches Repo kopieren |
| BananaMe | dateihashgeschützte Codeänderung, Verify/Recovery | Entwicklungs-/Agentenworkflow, nicht Produktlaufzeit | kein kundenseitiger Agent |
| StrawberryMe | Architekturbeobachtung und Verify, experimentell | Entwicklungs-/Architekturprüfung | kein Laufzeitdatenspeicher |

Die vorhandene FruitStack-Architektur (MariaDB, DuckDB, n8n, Ollama) kann wiederverwendet werden, **sobald** die echten Integrationsports und Security-Grenzen geprüft sind. Die Repositorien sind nicht automatisch ein gemeinsames installiertes Deployment.

## 5. Präzise Adapterverträge und Donor-Rollen

### D01 – Docling-Adapter

**Eingang:** tenant-scoped, geprüfte Dokumentreferenz; MIME, SHA-256, locale; kein unlimitierter Dateipfad.
**Ausgang:** Dokument-ID, Seitenanzahl, Tabelle/Text-Blöcke, Koordinaten/Fundstellen, Parser- und Modellversion, Warnungen, nicht erkannte Bereiche.
**Weitergabe:** ausschließlich ausgelesene strukturierte Dokumentfragmente an die lokale Vertragsregel-Extraktion. Ursprungsdokument bleibt revisionsfähiger Beleg.
**Tests:** synthetische 5-seitige Bonusvereinbarung mit einem Stufentableau und zwei Nachträgen; alle Betrags-/Schwellenfelder mit Seiten-/Zellenbeleg und signiertem Dokument-Hash. Fehlendes Feld -> REVIEW_REQUIRED.

### D02 – invoice2data-Adapter

**Eingang:** einzelne Lieferantengutschrift/Rechnung, ggf. freigegebene Vorlagen.
**Ausgang:** Lieferantentext, Beleg-ID, Datum, Dokumentart, Betrag, Währung, enthaltene Positionsdaten, Vorlagen-ID, Beleglink. Mehrdeutige Rechnungsnummer und OCR-Fehler führen zur manuellen Klärung.
**Tests:** Gutschrift und Storno zu derselben Boni-Periode; doppelte Datei darf keine doppelte Vergütungsbuchung auslösen.

### D03 – Frictionless-Adapter

**Eingang:** Upload-Dataset + ausdrückliches, versioniertes Tabellenschema.
**Ausgang:** Zeilen/Spalten-Fehler, Null-/Typ-/Vorzeichenfehler, normalisierte Daten und Verknüpfung zur Ausgangszelle.
**Tests:** ungültige CSV-Kodierung, deutsches Dezimalkomma, negatives Retoure-Vorzeichen, unerwartete Summen- und Datumsformats. Keine stillen Null-zu-Null-Euro-Reparaturen.

### D04 – RapidFuzz-Adapter

**Eingang:** Lieferanten-/Artikelkandidaten aus zwei Beständen plus bekannte IDs.
**Ausgang:** sortierte Vorschläge mit belegten Namen und Scores; **keine** automatische Identitätsentscheidung bei lediglich ähnlicher Schreibweise.
**Tests:** zwei ähnlich benannte Schwesterunternehmen mit verschiedenen Steuer-/Lieferantennummern werden nicht zusammengeführt. Freigaben sind auditierbar.

### Berechnungs-Engine – bewusst kein externer Donor

**Eingang:** validierte Vertragsregel (approved), signierter Daten-Snapshot, eindeutig zugeordneter Lieferant, Zeitraum, Rundungsregeln.
**Ausgang:** erwarteter Bonusbetrag (Decimal), Zwischensummen, alle berücksichtigten und ausgeschlossenen Transaktionen, Ausschlussgründe, Nachvollziehbarkeits-Hash.
**Regeln:** keine Float-Arithmetik; festgelegte Rundungsstelle und Reihenfolge; Versionierung bei Vertragsnachträgen, Teilperioden und Schwellenstaffeln; Reproduktion mit denselben Inputs.

### Recovery-Ledger – bewusst eigener Kern

**Eingang:** Finding Case + durch Kunden/ERP belegtes Realisation Event (Gutschrift, Zahlung, wirksame Verrechnung, Storno).
**Ausgang:** atomar fortgeschriebener, unverwechselbarer finanzieller Status und höchstens eine abrechenbare Netto-Basis pro wirtschaftlicher Realisierung.
**Tests:** parallele Webhook-Zustellung, doppelte Gutschrift, Rückbuchung, Teilbetrag und verspätete Bestätigung; niemals Doppelabrechnung.

## 6. Donor-Abnahme und Bezugsnachweise

Vor Integration für jeden Kandidaten **ein** dokumentierter Donor-Decision-Record:
1. Konkreter GitHub-Link und unveränderlicher Git-Commit oder Release-Tag.
2. Lizenzdatei, Laufzeitabhängigkeiten, Modellgewichte/Datensätze und NOTICE/THIRD_PARTY-Dateien; dokumentiertes kommerzielles Nutzungsrecht.
3. Sicherheit: SBOM, bekannte relevante CVEs, Provenienz, Pakete, keine Exfiltration; Laufzeit-Ressourcenlimits.
4. Contract-Test mit synthetischen Eingangs- und Erwartungsdateien plus bekannte Failure-Modes.
5. Gemessene Ergebnisqualität/Laufzeit/RAM am tatsächlichen Ausführungshost und konkrete Vorteile gegenüber Eigenentwicklung.
6. Entscheidung ADOPT / ADAPT / REFERENCE / REJECT, betroffene Dateien, verantwortliche Stelle, Prüfer und Rollback.

Keine Donor-Copy&Paste-Aktion ohne einen genehmigten Record. Für GPL-/AGPL-/MPL-Code kann der Record nur nach fallbezogener Prüfung zur tatsächlichen Codeübernahme führen.

## 7. Quelle/Lizenz/Stand

- https://github.com/docling-project/docling/blob/main/LICENSE
- https://github.com/invoice-x/invoice2data/blob/master/LICENSE.md
- https://github.com/frictionlessdata/frictionless-py/blob/main/LICENSE.md
- https://github.com/rapidfuzz/RapidFuzz
- https://github.com/camelot-dev/camelot
- https://github.com/opendataloader-project/opendataloader-pdf (v2.0+ Apache-2.0 beachten)
- https://github.com/dedupeio/dedupe/blob/main/LICENSE
- https://github.com/fastapi/fastapi
- https://github.com/pydantic/pydantic/blob/main/LICENSE
- https://github.com/py-pdf/pdf/blob/main/LICENSE
- https://github.com/OCA/connector und https://github.com/OCA/purchase-workflow
- https://github.com/frappe/erpnext; https://docs.frappe.io/cloud/marketplace/publishing-an-app-to-marketplace
- https://github.com/Dolibarr/dolibarr
- https://github.com/documenso/documenso
- https://github.com/docusealco/docuseal
- https://github.com/getlago/lago
- https://github.com/paperless-ngx/paperless-ngx
- https://github.com/pymupdf/PyMuPDF

**Forschungsstatus:** keine Donor-Library in LowHangingFruitMe installiert; keine Sicherheits-/Performancebenchmarks ausgeführt; genaue Release-Pins und eigene Lizenz-/Security-Abnahme sind bewusst noch offen.


## 8. Ergänzende Recherche: konkrete ERP-Connector-Donoren (02.11.2026)

Diese Projekte sind als **Implementierungsreferenz für einzelne Adapter**, nicht als komplette LowHangingFruitMe-Architektur zu verwenden. Lizenzdateien und GitHub-Metadaten wurden einzeln geprüft.

| ID | Repository | Beobachteter Stand/Lizenz | Konkrete Empfehlung |
|---|---|---|---|
| C01 | [weclapp/sdk](https://github.com/weclapp/sdk) | **Offizieller** TypeScript-SDK-Generator, MIT, nicht archiviert; erzeugt Typen/Services aus dem OpenAPI-Dokument der jeweiligen weclapp-Instanz | **Erster technischer SDK-Kandidat für weclapp**. Nur lesende Einkauf-/Supplier-/Credit-Endpunkte generieren/nutzen und Feldumfang in einem Testmandanten prüfen. Kein automatisches Schreibrecht |
| C02 | [Sysix/lexoffice-php-api](https://github.com/Sysix/lexoffice-php-api) | MIT, nicht archiviert; PHP 8.1+, PSR-18 HTTP-Client; laut README keine eingebauten Rate Limits oder umfassende Fehlerchecks | **Guter Referenz-/Clientdonor nur bei PHP-Portal/Adapter.** Bei geplantem Python-Kern nicht PHP allein wegen SDK einführen; offizielle Lexware REST-API direkt ansprechen |
| C03 | [Baebeca-Solutions/lexware-php-api](https://github.com/Baebeca-Solutions/lexware-php-api) | AGPLv3 im öffentlichen Code; Projekt bietet laut README eine **gesonderte kommerzielle Lizenz** (dort mit 200 EUR netto angegeben; vor Kauf erneut prüfen) | **Nicht unter AGPL in proprietären Service übernehmen.** Erst kommerzielle Lizenz bewerten, wenn tatsächlich eine PHP-Integration nötig ist |
| C04 | [marselsel/Lexware-MCP-Server](https://github.com/marselsel/Lexware-MCP-Server) | MIT, nicht archiviert; einzelmandantenbezogener MCP-Service mit Accounting-Tools | **Nur API-/Sicherheitsreferenz.** MCP-Agenten-Server ist für deterministischen, mehrmandantenfähigen Finance-Datenimport kein Ersatz für einen begrenzten Read-only-REST-Connector |
| C05 | [frappe/frappe-client](https://github.com/frappe/frappe-client) | MIT, aber **seit 31.03.2026 archiviert** | **Nicht als neue produktive Kernabhängigkeit.** Frappe-REST-API/aktuelle Framework-Dokumentation direkt verwenden oder aktiv gepflegten Client nach Lizenzprüfung auswählen |
| C06 | [Dolibarr/dolibarr](https://github.com/Dolibarr/dolibarr/blob/develop/htdocs/api/README.md) | offizieller REST-API- und ModuleBuilder-Code, GPL-3.0 | **D3 Referenz.** Für ein externes Tool API mit autorisiertem Benutzer-Token verwenden; eigenes Dolibarr-Modul als eigenständig GPL-konformes, dünnes Paket nur bei Bedarf |

**Integrationsempfehlung konkret:**

- Der zentrale LowHangingFruitMe-Service bleibt Python/FastAPI. Für Lexware Office **kein** zweiter PHP-Microservice nur wegen eines Libraries. Ein kleiner Python-REST-Client gegen https://developers.lexware.io/docs/ ist kürzer, besser kontrollierbar und vermeidet zusätzliche Laufzeit-/Lizenzlast.
- Bei weclapp ist ein kleiner TypeScript-Connector auf Basis des **offiziellen MIT-SDKs** sinnvoll, wenn die API-Discovery und Authentisierung am Tenant technisch möglich sind. Er sendet kanonische, minimal erforderliche Nutzdaten an unsere zentrale API.
- Der Frappe-Connector wird nicht auf ein archiviertes Python-SDK gegründet. Er nutzt Frappe-interne Dokument-APIs für die installierte App oder aktuelle offizielle HTTP-API-Routen für einen externen Client.
- Ein Odoo-/Dolibarr-Modul hat eigenen Releasezyklus, Lizenz, Security-Review und Store-Zulassung. **Keine** GPL-/AGPL-Codebasis wird in die proprietäre Rechenengine hineinkopiert.
- Weder MCP-Tools noch automatisch generierte SDKs garantieren Vollständigkeit der Einkaufs- und Bonusdaten; Datenfeld- und Periodenprüfungen bleiben zwingend.

**Primärquellen:**
- https://github.com/weclapp/sdk/blob/master/README.md und https://github.com/weclapp/sdk/blob/master/LICENSE
- https://github.com/Sysix/lexoffice-php-api/blob/development/README.md und https://github.com/Sysix/lexoffice-php-api/blob/development/LICENSE
- https://github.com/Baebeca-Solutions/lexware-php-api/blob/master/README.md und https://github.com/Baebeca-Solutions/lexware-php-api/blob/master/LICENSE
- https://github.com/marselsel/Lexware-MCP-Server/blob/main/README.md
- https://github.com/frappe/frappe-client (GitHub-Archivstatus)
- https://github.com/Dolibarr/dolibarr/blob/develop/htdocs/api/README.md
