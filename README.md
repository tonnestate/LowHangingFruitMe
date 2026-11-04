![LowHangingFruitMe – Neon-Banner](docs/Neon-Low-Hanging-FruitMe-Banner.png)

# LowHangingFruitMe

**B2B Revenue Recovery for FruitStack.** Ein eigenständiger, beleggestützter Prüfdienst für nicht vollständig realisierte Lieferantenboni und vertraglich eindeutige Einkaufskonditionen.

**Python-Version:** 0.13.1 (signierte Mappingfreigabe, harte R2-Semantik, messbare Audit-Datenqualität – Entwicklungsstand)  
**Marketing-Portal:** 0.1.0 (noch nicht deployed)  
**Status:** Bonusengine, ERP-Import mit HMAC-signierter, persistierter und widerrufbarer Mappingfreigabe, JWT-/MariaDB-geschützte Audit-API, scannerpflichtige private Upload-Staging-Schnittstelle, synthetisch getesteter authentifizierter Next.js-Arbeitsbereich, persistentes Recovery-Ledger (5%-Honorarvorschlag) und Kundenberichte als JSON/PDF/XLSX. **Weder API noch Website sind auf dem VPS deployed.** Kein produktiv freigegebener Kundendatei-Upload, keine Live-ERP-Anbindung, kein externer Piloterfolg und keine automatische abrechenbare Honorarrechnung.

## Eigenständige Website

Die deutsche Marketing-Website befindet sich unter [`portal/`](portal/README.md). Sie verwendet ausschließlich das vorhandene Originalbanner `docs/Neon-Low-Hanging-FruitMe-Banner.png`; beim Build werden aus den Originalpixeln die Markenfarb-Tokens und ein Messprotokoll erzeugt. Next.js (SSR/SSG) wird als isolierter Node-Dienst hinter einem **separaten Apache-VirtualHost** auf dem eigenen Server vorbereitet. WordPress und die Python-Finanzengine werden nicht verändert.

**Nachgewiesen:** [Website-GitHub-Actions 41607305839](https://github.com/tonnestate/LowHangingFruitMe/actions/runs/41607305839): Next.js-Build, Typprüfung, 7 Unit-Tests sowie 12 Chromium-Browsertests bei 1440/768/390 Pixeln bestanden. Noch **kein** Produktiv-Deployment und keine öffentlich freigegebene Annahme echter Kundendaten. Der authentifizierte Arbeitsbereich wird nur mit synthetischen Daten und isolierter Testinfrastruktur geprüft. Staging ist `noindex`/robots-disallowed.

[Website-Status und Grenzen](docs/WEBSITE_STATUS.md) · [Portal und lokaler Build](portal/README.md) · [Apache-/systemd-Vorlagen](deploy/).

Die Audit-Ergebnisse weisen nun drei erklärbare Datenqualitäts-Indikatoren aus: Abdeckung gegenüber bereitgestellten Kontrollzeilen, signierte Regelklarheit und Abgleich der Kontrollsummen. Fehlende Nachweise werden nicht als perfekte 100-%-Abdeckung dargestellt; die vollständige ERP-Quellenlage ist weiterhin **nicht** unabhängig bestätigt. R2-Schwellenvarianten werden nur mit explizit belegter und signierter Anwendungssemantik berechnet.

Die neue Preisentscheidung von 5 % gilt nur für neue Fälle ab v0.13.1. Bestehende Recovery-Fälle behalten ihren gespeicherten Satz von 3 %; diese Änderungen sind weder eine Kundenvertragsannahme noch eine Rechnungsfreigabe. SQL-Migration `sql/007_recovery_fee_policy.sql` muss vor Nutzung des aktualisierten Recovery-Ledgers eingespielt werden.

## Was funktioniert

- Deterministische Berechnung von Jahresboni, rückwirkenden und marginalen Staffeln sowie festen Schwellenprämien; Dezimalarithmetik, Retouren, Gutschriften, Stornierungen und eindeutige Vertragsperioden.
- **ERP-unabhängiger Import:** Erkennung und Spaltenvorschläge für CSV- und XLSX-Exporte; XML-Rechnungen, PDF und DOCX werden zunächst nur dem Dokumentenweg zugeordnet. Erst ein explizit bestätigtes Spaltenmapping erzeugt kanonische Buchungsdaten mit Originaldatei-Hash und Zeilenherkunft. Noch keine Lexware-, Odoo-, SAP-, Sage-, NetSuite- oder P21/Eclipse-Connectoren.
- Einlieferung kanonischer Einkaufs- und Gutschriften-CSV mit **Frictionless** als echtem Schema-Prüfer und anschließend strenger fachlicher Validierung; Herkunftsverweise auf Datei-Hash und Quellzeile.
- **Freigabenachweis:** Vertragsregel und konkrete Dokumentdatei werden per SHA-256 mit einer HMAC-signierten Bestätigung verknüpft. Der CSV-Pfad verlangt Mandanten- und Gesellschaftsbindung; `approved: true` allein genügt nicht. Keine produktive Prüfer-Authentifizierung oder Widerrufsverwaltung.
- **Verifizierte Access-Tokens:** RFC-9068-kompatible RS256-Signaturprüfung anhand einer vertrauenswürdig bereitgestellten öffentlichen JWKS, Prüfung von Aussteller, Audience, Client-ID, Gültigkeit und Berechtigungsumfang. Eine durch MariaDB berechtigte Person kann Regeln über `AuthenticatedApprovalService` freigeben, widerrufen und eingeschränkte Audits starten. **Noch keine Live-IdP-Anbindung; schmale HTTP-API für bereits sicher bereitgestellte Datenpakete vorhanden, kein öffentlicher Upload.**
- **Private Dateiannahme v0.9:** `POST /v1/uploads` (15-Minuten-Absicht), `PUT /v1/uploads/{id}/content` (begrenzter Rohdatenstrom) und `GET /v1/uploads/{id}` (Status), mit JWT-/Mandantenprüfung, exakten Bytes und SHA-256, verpflichtendem ClamAV-Scanner-Verdikt und geprüfter Dateiklassifikation. **Erfolgreich gescannte Dateien sind noch keine freigegebenen Auditquellen. Kein echter ClamAV-Betrieb auf dem VPS.** [Dokumentation](docs/UPLOAD_INTAKE.md).
- **Kundenberichte v0.12:** Nach über alle Gates erfolgreich ausgeführtem Audit: autorisierte PDF-/XLSX-/JSON-Ausgabe mit Quellen-Hash, Differenzbetrag und 5%-Honorarvorschlag, herunterladbar über den geschützten Next.js-Arbeitsbereich. Kein öffentlicher Link und keine Rechnung.
- **Recovery-Ledger v0.11/v0.12:** MariaDB-Fälle, idempotente Realisierungs-/Stornoereignisse mit Beleg-Upload, unabhängige Finanzprüfung, Fallstatus NONE/CLAIMED/REALIZED_PARTIAL/REALIZED_FULL/DISPUTED/CLOSED, 5%-Honorarvorschlag. Rechnungsfreigabe und `fee_due_net` fehlen absichtlich.
- **Authentifizierte Audit-API v0.8:** `POST /v1/audits` und `GET /v1/audits/{id}` für serverseitig registrierte, SHA-256-geprüfte private Quellen. JWT/Reviewer-Grants, MariaDB-Idempotenz, Quellen-Snapshots und Berichtsspeicherung sind gegen synthetische Daten getestet. **Keine öffentliche Kundendatenannahme und kein VPS-Deployment.**
- **Persistierte Freigaben:** Genehmigungen werden in MariaDB registriert, mandantenbezogen freigegeben oder widerrufen und während der Berechnung durch `SELECT ... FOR UPDATE` vor konkurrierenden Änderungen geschützt. Ohne Registry läuft kein finaler CSV-Audit.
- **Readiness-Gate:** separate ERP-Kontrollsummen für Anzahl und Nettobetrag, Scope-Kontrolle für Lieferant/Vertrag/Periode, Status `READY_FOR_AUDIT` / `LIMITED` / `NOT_READY`. Bei fehlenden oder widersprüchlichen Kontrollen entsteht kein abschließender Geldbefund.
- Lokale PDF-Extraktion über **Docling** in belegbare Segmente (Text/Tabellen, Seite, Hash), ausdrücklich **ohne automatische Vertragsregel-Freigabe**.
- Wiederholbare synthetische Regressionstests, GitHub Actions für Python 3.11/3.12, getrennte Entwicklungs- und Betriebsgrenzen.
- Jeder Bericht trennt rechnerische Differenz, unsichere Datenlage und tatsächlich realisierte sowie abrechenbare Erfolge.

## Installation und reproduzierbarer lokaler Test

Python >= 3.11; die reine Rechenengine benötigt keine externen Runtime-Abhängigkeiten.

~~~bash
python -m pip install -e ".[import,registry,auth,universal,api]"
python -m unittest discover -s tests -v
python -m lowhangingfruitme.cli tests/fixtures/flat_rebate.json
~~~

Dateien vorab klassifizieren – ohne ERP-Verbindung und ohne automatische Freigabe:

~~~bash
lhfm inspect-source --file tests/fixtures/transactions.csv --dataset transactions
~~~

Beliebig benannte CSV-/Excel-Spalten können mit einer **zuvor geprüften und bestätigten Mapping-Datei** normalisiert werden. Der neue Befehl `lhfm normalize-source --file <export.csv> --dataset transactions --source-system erp --plan <mapping.json> --output <kanonisch.csv>` schreibt nur in eine neue Datei und überschreibt keine vorhandenen Daten. Siehe [Universal Import](docs/UNIVERSAL_IMPORT.md).

Für einen **bereits signierten** Vertragsbeleg bietet `lhfm audit-sources` einen Aufruf von geprüftem CSV-/XLSX-Mapping über die bestehenden Freigabe- und Vollständigkeits-Gates bis zum JSON-Report. Er erzeugt **keine** eigene Vertragsfreigabe. [Vier-Wochen-Abnahmestand](docs/FOUR_WEEK_ACCEPTANCE.md) · [synthetischer Goldstandard](docs/PILOT_GOLDSTANDARD.md).

CSV-End-to-End-Prüfung mit **synthetischen** Dateien:

~~~bash
# AUSSCHLIESSLICH FÜR SYNTHETISCHE TESTDATEN IN ISOLIERTER MARIADB.
# Vorher MariaDB lhfm_test bereitstellen, LHFM_DB_HOST/PORT/USER/PASSWORD/NAME
# ausschließlich als Test-Credentials konfigurieren, und:
python tests/scripts/setup_approval_registry.py
# CI erhält einen frischen Zufallsschlüssel.
export LHFM_APPROVAL_KEY_HEX="$(python -c 'import secrets; print(secrets.token_hex(32))')"
python tests/scripts/make_synthetic_approval.py \
  tests/fixtures/rule.json tests/fixtures/synthetic_agreement.txt /tmp/lhfm-approval.json
lhfm audit-csv \
  --rule tests/fixtures/rule.json \
  --transactions tests/fixtures/transactions.csv \
  --settlements tests/fixtures/settlements.csv \
  --source-system erp \
  --controls tests/fixtures/source_controls.json \
  --approval /tmp/lhfm-approval.json \
  --contract-source tests/fixtures/synthetic_agreement.txt \
  --tenant-id T-SYN-1 \
  --legal-entity-id LE-SYN-1 \
  --confirm-transactions-complete \
  --confirm-settlements-complete \
  --confirm-agreements-complete
~~~

Der lokale CLI-Testgenerator registriert nur **synthetische Prüfbelege unter einem fiktiven Datenbankrollen-Eintrag ohne echte IAM-Authentifizierung** und darf niemals öffentlich als Freigabe-Endpunkt eingesetzt werden. Ein unfreigegebener Direktlauf der JSON-Kalkulationsengine bleibt `REVIEW_REQUIRED` und liefert keinen Status `EVIDENCED`.

Die drei Bestätigungen sowie die Kontrollsummen sind **explizite externe Angaben** und kein unabhängiger ERP-Vollständigkeitsbeweis. Ohne Kontrollsummen gibt die CSV-CLI lediglich eine Readiness-Diagnose aus und erzeugt keinen berechneten Differenzfall. Ohne diese Bestätigungen liefert der Audit lediglich einen Prüfstatus mit Einschränkungen. Bei vollständig bestätigtem synthetischem Beispiel: 200.000 EUR anrechenbarer Nettobezug, 2 % Bonus, 1.500 EUR Gutschrift → 2.500 EUR **rechnerische Differenz**, 0 EUR automatisch abrechenbares Erfolgshonorar.

Docling separat installieren und lokal ein PDF unter Vorbehalt der Sicherheitsbedingungen prüfen:

~~~bash
python -m pip install -e ".[docs]"
lhfm extract-pdf --file /path/to/your/local-contract.pdf
~~~

**Achtung:** Der Docling-Adapter ist ein lokaler Prototyp ohne isolierten Upload-Worker, echte OCR-Qualitätsabnahme oder garantierte Offline-Modellbereitstellung. Keine Kundendokumente vor Prüfung des Host-Sicherheitskonzepts verarbeiten.

## Produktarchitektur

Eigenständiges Marketing-Portal (**gebaut, nicht deployed**) / geschützter Dateiupload (**Staging implementiert, keine Portalanbindung oder Datenfreigabe**) und ERP-Connector (**geplant**) → begrenzte, authentifizierte REST-API (**entwickelt; nur operatorseitig registrierte Datenpakete**) → Intake-Adapter (CSV-Frictionless/PDF-Docling) → bestätigte Vertragsregel → deterministischer Audit → belegte Differenzakte → Recovery-Ledger und erfolgsabhängige Abrechnung (**geplant**).

Es wird **kein** eigenständiges ERP oder FruitStack-Orchestrierungssystem dupliziert. Kernberechnung und Datenimport sind plattformunabhängig. Lexware, weclapp, Odoo, ERPNext/Frappe, Dolibarr und Oro sind recherchierte Integrations-/Distributionsziele; sie sind **nicht produktiv angebunden**.

## Geschäft und Grenzen

Angedachtes Kundenangebot: eine einmalige Prüfung gegen **5 % von der nachweislich, zurechenbar und wirtschaftlich tatsächlich realisierten zusätzlichen Nettovergütung**. Erfolgshonorar, RDG-Abgrenzung, Datenschutz und Vertragstexte sind vor kommerziellem Start extern rechtlich zu prüfen. Das Produkt betreibt im ersten Umfang weder Inkasso noch autonomes Forderungsmanagement.

## Dokumentation

- [Fach- und Architekturkonzept](docs/CONCEPT.md)
- [Donorenregister und Lizenzgrenzen](docs/DONORS.md)
- [Kanonischer Datenvertrag und API-Spezifikation](docs/API_AND_DATA.md)
- [Vertrags- und Vergütungsmodell](docs/LEGAL_AND_REVENUE.md)
- [Lieferplan und Abnahmekriterien](docs/DELIVERY_PLAN.md)
- [Tatsächlicher Implementierungsstand](docs/IMPLEMENTATION_STATUS.md)
- [Prüfkriterien und Kontrollsummen für Data Readiness](docs/DATA_READINESS.md)
- [Signierte Regel-Freigaben und ihre Grenzen](docs/RULE_APPROVAL.md)
- [MariaDB-Freigaberegister, Widerruf und transaktionale Sperre](docs/APPROVAL_REGISTRY.md)
- [Authentifizierung und JWT-Trust-Boundaries](docs/AUTHENTICATION.md)
- [Universeller ERP-Export-Import und Vertrauensgrenzen](docs/UNIVERSAL_IMPORT.md)
- [Audit-HTTP-API v0.8, Aufrufvertrag und Sicherheitsgrenzen](docs/AUDIT_API.md)
- [Private Dateiannahme v0.9 – Malware-Scan und Trust-Boundary](docs/UPLOAD_INTAKE.md)
- [Release-Evidenz](EVIDENCE.md), [Changelog](CHANGELOG.md), [Sicherheit](SECURITY.md), [Agentenvorgaben](AGENTS.md), [Drittherstellerhinweise](THIRD_PARTY_NOTICES.md)

Das öffentliche Repo enthält ausschließlich eigene Implementierung und synthetische Testdaten. Es wurden keine Fremd-ERP-Quelltexte kopiert. Für das Projekt wurde noch **keine Open-Source-Distributionslizenz festgelegt**; öffentlich lesbarer Code ist nicht automatisch frei zur Weiterverwendung.

### Laufende Weiterentwicklung: sichere Vertragsregel-Revisionen (v0.14 in Arbeit)

Der bestehende signierte MariaDB-Freigabepfad wurde um eine aktuelle Revision je Mandant, Gesellschaft, Vertragsnummer und Regel-ID erweitert. Eine neue fachlich signierte Freigabe sperrt die vorherige für **neue** Audits; historische, bereits abgeschlossene Auditberichte bleiben lesbar. Die Sperre wird durch eine Datenbanksperre auf den Revisionskopf gegen gleichzeitige Freigaben und Audit-Ausführung geschützt. Das Datenbank-Upgrade erfolgt ausschließlich kontrolliert mittels `sql/008_rule_revisions.sql`, nicht beim API-Start. Altbestände ohne Revisionszuordnung müssen sicher neu freigegeben werden. Vollständiger Vorschlags-Lifecycle (EXTRACTED/NEEDS_CONFIRMATION), reale Nachtragsannotation und Kundenpilot sind noch offen; der Produktrelease bleibt v0.13.1 bis zur Abnahme.


### Verbindlicher MariaDB-Preflight (nicht migrationsausführend)

Vor einem API-Start müssen die dedizierten MariaDB-Migrationen `sql/001` bis
`sql/008` durch einen berechtigten Operator in kontrollierter Reihenfolge
installiert werden. **Nie DDL auf einem API-Request oder automatisch beim Start.**
Nach Backup und freigegebener Migration die vorhandenen DB-Umgebungsvariablen
setzen und die ausschließlich lesende Prüfung ausführen:

~~~bash
lhfm-schema-check
~~~

Die FastAPI-Factory `create_app_from_environment()` führt dieselbe Prüfung
verbindlich aus und verweigert den Start, wenn Tabellen, wesentliche Spalten,
Constraints, InnoDB-Engine oder der historische 3%-Default fehlen. Dabei werden
**keine** alten Freigaben stillschweigend auf v0.14 hochgezogen und keine
Produktivdaten geändert. Der Check ersetzt keine Betreiberfreigabe, kein
Datenbankbackup, keinen Migrations-Runner und keine reale Pilotabnahme.


### Kontrollierter SQL-Migrationsprozess (nicht beim API-Start)

`lhfm-migrate --sql-dir /absoluter/pfad/zum/sql` zeigt ausstehende Migrationen
**nur lesend**. Der Prozess prüft die gespeicherten SHA-256-Prüfsummen der
ursprünglichen SQL-Dateien, lässt keine Lücken oder erneut gestartete
Teil-Migrationen zu und verweigert die Übernahme bereits vorhandener Tabellen
ohne überprüfbaren Migrationsverlauf.

Vor produktiver Migration: Anwendung stoppen, Backup erstellen und dessen
Wiederherstellung testen, Datenbankrechte und SQL-Dateien überprüfen. Nur nach
Freigabe durch den Betreiber:

~~~bash
LHFM_MIGRATION_APPROVED=YES lhfm-migrate --sql-dir /absoluter/pfad/zum/sql --apply --backup-confirmed
lhfm-schema-check
~~~

Der Runner nutzt einen MariaDB-Advisory-Lock gegen konkurrierende Migrationen.
MariaDB-DDL ist nicht transaktional rollbackfähig: ein unterbrochener Lauf
bleibt **IN_PROGRESS** im Ledger und verhindert einen stillen Retry bis zur
manuellen DBA-Reconciliation. Das Schema muss nach dem Upgrade die Versionen
001–008 als angewendet ausweisen, andernfalls verweigert die FastAPI den Start.
Kein automatisches Upgrade fremder oder bereits ungeprüft manuell migrierter
Produktivbestände. Die isolierte CI-Testdatenbank wird durch denselben Runner
initialisiert. Die Dokumentation behauptet weiterhin **keine** reale
VPS-Migration oder Kundenfreigabe.


### Laufzeit-Gate vor Load-Balancer-Freigabe

`GET /healthz` bestätigt ausschließlich einen lebenden API-Prozess. Das neue
`GET /readyz` liefert nur dann HTTP 200, wenn Finanzdienste und MariaDB-Schema
verfügbar sind und ClamAV über seinen lokalen UNIX-Socket ein korrektes
`zPING`/`PONG`-Protokoll beantwortet. Fehlende/gestörte Komponenten liefern
HTTP 503, ohne interne Pfade offenzulegen. Ein Ping bestätigt **nicht** die
Aktualität der Virensignaturen oder die Betriebssicherheit der PDF-Parser;
diese Punkte bleiben separate Go-Live-Kontrollen.


### JWT-Public-Key-Rotation

Die vorhandene OIDC-Ressourcenserverprüfung lädt aktualisierte, vertrauenswürdig
auf dem Host **atomar ersetzte** JWKS-Dateien ohne API-Neustart. Das
Dateimanagement bleibt eine Betreiberaufgabe; defekte oder fehlende Schlüssel
führen zu abgewiesener Authentifizierung, nicht zu einem unsicheren Fallback.
Ein realer Identity Provider, die Refresh-Token-Verwaltung und das
Benutzer-Offboarding sind weiterhin nicht abgenommen.


### Unveränderliche SQL-Release-Prüfsummen

Die API prüft nicht mehr nur das Schema und das Format der gespeicherten
Migrationshistorie, sondern vergleicht jede eingetragene SHA-256-Prüfsumme mit
der im Release **fest hinterlegten** SQL-Baseline. Der Installer verweigert
bereits vor Ausführung die Verwendung veränderter historischer SQL-Dateien.
Bei neuen Migrationen werden ausschließlich neue Versionsnummern ergänzt;
bestehende Hashes dürfen nicht automatisch neu berechnet werden. Das ist
kein Ersatz für Git-Signaturen, Datenbank-Backup und kontrollierten Restore.


### v0.14 – dokumentengebundene Vertragsfreigabe (Pilotcode)

Der geschützte Kundenpfad benötigt für neue Audit-Bundles einen unveränderlich
referenzierten Vertragskandidaten. Ein bereits ClamAV-geprüftes PDF wird mit
Docling im getrennten, ressourcenbegrenzten Python-Unterprozess ausgelesen.
Die extrahierten Originalfundstellen werden mit dem SHA-256-Hash des
hochgeladenen Dokuments und einem Mandanten-/Gesellschafts-/Reviewerbezug
registriert. Der Prüfer muss die konkrete Klausel auswählen und die abgeleitete
Regel bestätigen. Erst die bestehende signierte MariaDB-Regeltransaktion darf
`NEEDS_CONFIRMATION → APPROVED` umstellen; Nachträge ersetzen ältere
Freigaben, Widerrufe bleiben nachvollziehbar.

SQL-Migration `009_contract_candidates.sql` gehört zur kontrollierten,
prüfsummengebundenen Releasefolge. Direkte Alt-Testfreigaben ohne Kandidat
bleiben **ausschließlich in als synthetisch markierten Tests** möglich.
Die tatsächliche Docling-Modellinstallation und vom Netz getrennte
Parser-Ausführung sowie authentifizierte Unternehmenszugänge sind vor
Produktivstart zu verifizieren. Siehe `docs/GO_LIVE_GATE.md`.


Die technisch synthetisch bestandene v0.14-Kandidatenstrecke ersetzt **keine**
Freigabe für echte Vertragsdaten oder Kundenzahlungen. Die konkreten externen
Produktionsgates G0–G5 sind unter `docs/GO_LIVE_GATE.md` verbindlich festgehalten.
