# Implementation status – LowHangingFruitMe v0.13.1

**Stand:** 03.11.2026. Produktentwicklung, kein kommerzieller oder produktiver Betrieb. Der aktuelle Revisionsnachweis steht in [EVIDENCE.md](../EVIDENCE.md); keine behaupteten Live-Kunden- oder ERP-Erfolge.

## Preisstand 0.13.1 (03.11.2026)

Neue Recovery-Faelle speichern 500 Basispunkte (5 %) dauerhaft bei Anlage; der SQL-Nachtrag `007_recovery_fee_policy.sql` vergibt 300 Basispunkte an bereits vorhandene historische Faelle. Kundenbericht und Portal zeigen den pro Fall gespeicherten Satz; alte Berichte/Faelle werden nicht rueckwirkend neu bepreist. Die untenstehenden v0.11/v0.12-Beschreibungen mit 3 % sind historische Funktionsbeschreibungen. Dies ist weiterhin **nur ein unverbindlicher Honorarvorschlag**; `fee_due_net=0.00` ohne dokumentierten Vertrag/Rechnungsfreigabe. Noch keine produktive Migration, kein echter Kunde, keine externe Rechtspruefung.

## Implementiert

**Deterministische Bonusengine 0.1.0:** Regelarten FLAT_RATE, RETROACTIVE_FULL_BASE, MARGINAL_PER_TIER und FIXED_THRESHOLD_REWARD; Decimal-Rechnung; Retouren, Gutschriften und Rückbuchungen; Lieferanten-/Perioden-/Währungsprüfung; separate Review-/Fehlerzustände; reproduzierbarer Snapshot-Hash. Der Report behauptet weder juristisch gültige Forderungen noch abrechenbare Erlöse.

**CSV-Import v0.2.0:** Strikte kanonische Header für Einkaufstransaktionen und Gutschriften, Validierung mit Frictionless plus Domain-Parser, Dateisignatur-SHA256/Zeilenfundstellen, keine automatischen Schema- oder Zahlenkorrekturen, Duplicate-ID-Ablehnung, lokale End-to-End-CLI zur bestehenden Engine.

**PDF-Extraktionsadapter v0.2.0:** Lokale PDF-Annahme mit einfachen Dateisignatur-/Größenkontrollen, Docling-Dokumentkonvertierung und Quellenverweisen auf Datei-Hash, Segment und Seite. Das Ergebnis ist stets NEEDS_HUMAN_REVIEW; kein Extraktionsresultat erzeugt eigenmächtig eine freigegebene Bonusregel.

**Repository:** installierbares Python-Paket, getrennte optionale Abhängigkeiten, GitHub Actions Matrix, synthetische Testdateien, AGENTS.md, SECURITY.md, CHANGELOG.md, EVIDENCE.md, THIRD_PARTY_NOTICES.md und ausführliche Konzept- und Donor-Dokumentation.

**Data-Readiness-Gate v0.3.0:** Strikte Überprüfung des freigegebenen Vertrags, von Lieferant/Währung/Periode, eindeutig zugeordneten Buchungen sowie Vergleich von Zeilenanzahl und Nettosummen mit einem separat gelieferten Kontrollreport. Ohne Kontrollen liefert der CSV-Pfad nur einen eingeschränkten Diagnosebericht, bei Abweichung keine Bonusberechnung. Die Quelle und Verlässlichkeit des separat gelieferten Reports werden noch nicht unabhängig verifiziert; auch READY_FOR_AUDIT ist daher keine Zusicherung kaufmännischer Datenvollständigkeit.

**Regelfreigabe v0.4.0:** HMAC-SHA256-signiertes Freigabereceipt mit festem Regelhash, freigegebenem Originaldokument-Hash, tenant_id, legal_entity_id, reviewer_id, reviewer_role, source_revision_id, approval_id und Zeitstempel. CSV-Intake und Data-Readiness prüfen die Signatur gegen einen geheimen, nur serverseitig bereitzustellenden Schlüssel und vergleichen Regel, Mandant/Gesellschaft und tatsächlich eingelesene Vertragsdatei. Ohne verifizierten Beleg kein finaler Auditstatus. Die direkte reine Rechenengine meldet bei fehlender Autorisierung `REVIEW_REQUIRED`, selbst bei `approved=true`. CI-Testfälle sind rein synthetisch.

**Freigaberegister v0.5.0:** MariaDB-InnoDB-Tabellen für tenant-/gesellschaftsgebundene Reviewer-Grants, unveränderlichen Genehmigungsinhalt, ACTIVE/REVOKED-Zustand und ISSUED/REVOKED-Ereignisse; SQL-basierter Statusabgleich und Rollenscope bei Registrierung und unmittelbar am Audit-Dispatch. Gleichzeitiger Widerruf wartet auf den transaktionalen `SELECT ... FOR UPDATE`-Abschnitt des Audits. Ohne Registry erzeugt das CSV-Interface keine finalen Geldbefunde.

**JWT-Authentifizierung v0.6.0:** Standardsbasierte RS256-Prüfung von OAuth-Access-Tokens (nicht ID-Tokens) mit vordefinierter issuer-/audience-/client-ID-Bindung, fester öffentlicher JWKS und maximaler Gültigkeitsdauer. `AuthenticatedApprovalService` koppelt die verifizierte Tokenidentität mit aktiven MariaDB-Reviewer-Grants, schränkt Freigabe/Widerruf auf konkrete Rechte ein und führt bei Audit-Ausführung einen erneuten Tokencheck im bereits transaktional geschützten Dispatch aus. Die echte RSA-/MariaDB-Kombination ist mit synthetisch generierten Schlüsseln in CI getestet. Kein realer Identity-Provider verbunden.

**Universeller ERP-Export-Import v0.7.0:** Neue lokale Bibliothek `universal_import.py` erkennt CSV (UTF-8, Komma/Semikolon/Tab), XLSX (explizite Blattauswahl, Formeln blockiert) sowie XML-Rechnungen, PDF und DOCX zur **weiteren Klassifizierung**. Ein Vorschlagsmapping von deutschen und englischen Spaltennamen kann geprüft und ausdrücklich bestätigt werden. Eine an den SHA-256-Hash der Originaldatei gebundene Mappingfreigabe normalisiert belegreferenzierte Einkaufs-/Gutschriftenlisten; anschließend wird der bereits getestete Frictionless/Readiness/HMAC/MariaDB-Auditpfad aufgerufen. Keine automatische Extraktion aller XML-Rechnungsposten, keine vollautomatische Vertragsregelinterpretation, keine echten ERP-Connectoren, keine sichere öffentliche Upload-API. Die Mapping-Bestätigung ist zunächst eine Benutzerangabe, kein kryptografischer Reviewer-Nachweis.

**Öffentliche Website – eigener Stand `portal@0.1.0` (03.11.2026):** Deutsches Next.js-Frontend als isolierter Webdienst vorbereitet; Startseite, Lieferantenboni, Marge, O2C, Service, Preis/Ablauf, Eignungscheck, Bonusstaffeln, Bonusgutschriften, Wissensindex und fünf eigenständige Fachartikel. Originales Banner aus `docs/` ohne Bildkopie im Repository; Build-Pipeline erstellt unveränderte Bildkopie und CSS-Markenfarben anhand der tatsächlichen PNG-Pixel. Responsive Browser- und Interaktionstests 1440/768/390 bestanden, inklusive Navigations-, FAQ-, Rechner-, 404- und noindex/robots-Prüfungen. Neue Apache-/systemd-Konfigurationsvorlagen **nicht** auf den Produktivserver installiert. Die Portal-Website ist weiterhin nur Marketing und nicht an die nun separat vorhandene, noch nicht deployte Audit-API angeschlossen. Aktuelle Rechtsseiten sind ausdrücklich Staging-Platzhalter. Vollständige Details: `docs/WEBSITE_STATUS.md`.

**FastAPI-Audit-Schnittstelle v0.8.0 (03.11.2026):** `GET /healthz`, `POST /v1/audits`, `GET /v1/audits/{id}` als separate, noch **nicht installierte** Python-App. RFC-9068-Access-Token plus aktiver MariaDB-Reviewer-Grant erforderlich; nur serverseitig registrierte private Quellenbündel mit Original-SHA256 und signergebundener Regel/Dokumentfassung. Idempotente (auch parallelitätsgetestete) MariaDB-Auftragsreservierung, private Laufzeitkopien, normaler Frictionless/Readiness/HMAC/Registry-Gate, gespeicherter Bericht und reviewer-/tenant-/gesellschaftsgebundene Abfrage. Es gibt **keine** per HTTP angebotene Dateispeicherung/Dateipfadübergabe, keine reale Kundenregistrierung, keinen Produktions-IdP und keinen Queue-Worker. Ausführung aktuell synchron, auf synthetische Daten begrenzt. [Technischer API-Vertrag](AUDIT_API.md).

**Private Upload-Staging-API v0.9.0 (03.11.2026):** Authentifizierte `POST /v1/uploads`, `PUT /v1/uploads/{id}/content` und `GET /v1/uploads/{id}` mit `lhfm:upload:write`-Scope und aktiven MariaDB-Reviewer-Grants. Einmalige 15-Minuten-Uploadabsicht, Dateigrößenlimit 16 MiB, exakte Byteanzahl und SHA-256, exklusive private 0600-Staging-Datei, Scannerpflicht mit lokalen ClamAV-UNIX-Socket-Instream-Frames, danach Dateisignatur-/XML-/Office-Prüfung und eindeutige, nicht überschreibbare private Ablage. Mehrfache Uploadversuche, Parallelschreiben, falsche Mandanten, ungültige Bytes, schädliche XML-Strukturen und Scanner-Ausfall werden getestet abgewiesen. Das CI verwendet einen **synthetischen Scan-Entscheider** plus simulierten ClamAV-UNIX-Socket, keine echte ClamAV-Installation oder produktive Infrastruktur. `CLEAN` heißt nur transporttechnisch geprüft; `usable_for_audit=false`, weil der separate Freigabe-/Normalisierungs-/Kontrollschritt noch fehlt. Kein geschütztes Browserportal, kein realer IdP, keine Datenverschlüsselung oder automatische Löschung. [Upload-Spezifikation](UPLOAD_INTAKE.md).


**Geprüfter Kundendownload und Recovery-Ledger v0.11–0.12 (03.11.2026):** Die FastAPI-Routen und das Next.js-BFF unterstützen nach geprüfter JWT-/Rollen-/Mandantenzugehörigkeit PDF-, XLSX- und JSON-Kundenberichte für tatsächlich `EVIDENCED` ausgeführte Audits. Die API trennt `calculated_variance_net`, bestätigte aber nur durch einen unabhängigen Finance-Actor **manuell attestierte** Realisierung, die daraus errechnete **3-%-Honorarprognose** und `fee_due_net` = 0 bis zu einer späteren ordnungsgemäßen Rechnungsfreigabe. Auf der Recovery-Seite existieren persistierte idempotente und beleggebundene REALIZATION-/REVERSAL-Events, eine zweite Finance-Freigabe und die Statuswerte NONE, CLAIMED, REALIZED_PARTIAL, REALIZED_FULL, DISPUTED, CLOSED. Für DISPUTED/CLOSED/OPEN gibt es append-only Finance-Statusereignisse und einen separaten HTTP-Operator-Endpunkt. **Weder Rechnungsfreigabe noch tatsächliche Bankzahlung werden softwareseitig unabhängig nachgewiesen.**

**Ein-Befehl-Lauf v0.12.0:** `lhfm audit-sources` nimmt zwei bereits fachlich geprüfte Mapping-Pläne und eine zuvor separat signierte, in MariaDB registrierte Vertragsfreigabe entgegen; führt beide ERP-Listen auf den bestehenden unveränderten kanonischen Pfad und berechnet mit Readiness-/Registry-Prüfung einen Gesamtbericht. Kein eigenmächtiges Erteilen der Vertragsgenehmigung per CLI.

**Portal:** Der vorhandene Next.js-Arbeitsbereich ist OIDC-geschützt, verfügt über einen serverseitigen BFF-Allowlist-Proxy für die tatsächlichen FastAPI-Routen und bietet Upload, Mapping, Regelbestätigung, Audit, Recovery und Bericht-Download. *Nur synthetisch im isolierten CI-/Entwicklungsstand getestet*, keine echte externe Kundenanmeldung oder Browser-zu-VPS-Kundenabnahme.

**Signierte Mappingfreigabe v0.13.0 (03.11.2026):** `sql/006_mapping_approvals.sql` und `mapping_approval.py` speichern gesonderte HMAC-receipts für Einkaufs- und Gutschriftenmapping, jeweils gebunden an Bundle, Originaldatei-Hash, Mapping-Hash, Regel-Freigabe-ID, Mandant, juristische Einheit und verifizierten Reviewer. Active/Revoked-Ereignisse werden append-only protokolliert. Der bestehende `/v1/audits`-Pfad sperrt beide Mappingdatensätze beim Dispatch und ruft **darunter** die bestehende signierte Vertrags-/Readiness-Prüfung auf. Kein öffentliches unsigniertes Mapping kann als Customer-Audit gelten. Der Ein-Befehl-CLI-Pfad bleibt eine **lokale Operator-Schnittstelle** mit zuvor geprüften Plänen; die separate kryptografische Mappingfreigabe gilt im HTTP-Upload/Bundle-Pfad. Bestehende manuell operatorprovisionierte Bundles ohne Upload-Provenienz bleiben gesondert vertrauensgebunden.

**Harter R2-Parser-Gate v0.13.0:** `BonusRule.load` verlangt für Staffelregeln ein explizites `tier_semantics`-Objekt mit `application` (`FULL_BASE`, `EXCESS_ONLY`, `BANDS`, `FIXED_REWARD`), `reviewed=true` und `evidence_ref`, die in den freigegebenen Vertragsfundstellen enthalten sein muss. Ein Überschussmodus kann nur genau eine Schwelle, ein Bandmodell mindestens zwei Intervalle deklarieren. Falscher Typ, semantischer Widerspruch oder fehlende Fundstelle werden **vor der Bundle-Promotion** mit `RULE_SEMANTICS_NEEDS_REVIEW` als HTTP 422 abgewiesen. HMAC-Bindung umfasst die genaue Anwendung und Klausel; kein automatisches Modell darf daraus eigenmächtig ein Staffelrecht machen.

**Qualitätskennzahlen v0.13.0:** Readiness liefert `quality_metrics` mit Zähler/Nenner für importierte Zeilen gegenüber bereitgestellten ERP-Kontrollen, booleschen Reconciliation-Ergebnissen für die zwei obligatorischen Prüfreports und der eindeutigen freigegebenen technischen Regel-Semantik. Jeder Wert enthält Herkunfts- und Unsicherheitsgrenzen; fehlende Nenner werden `null`, nicht geschätzt. `value_weighted_source_coverage_pct` ist mangels echter wertgewichteter Ausgangsbasis bewusst `null`. Die drei Quoten, einschließlich den `issues[].code`-Blockern, werden im Next.js-Arbeitsbereich angezeigt und sind in Kunden-JSON, PDF und XLSX enthalten. **Quoten haben keinerlei Wirkung auf `audit_admissible`.** Dies ist ein synthetisch getesteter Entwicklungsstand, keine Betriebsabnahme.

## Ungeprüfte Aspekte und klare Grenzen

- GitHub Actions ist der tatsächliche Testnachweis; nicht jede neu geschriebene Testdatei wurde lokal ausgeführt. Ergebnisse mit Run-ID in EVIDENCE.md festhalten.
- Docling wurde noch nicht anhand echter annotierter Vertragsdokumente in einer isolierten Produktionsumgebung benchmarkgetestet. Docling selbst ist noch kein Beleg für ein vollständig funktionierendes Dokumentenprodukt.
- XLSX und flexibel benannte CSV lassen sich mit **manuell bestätigtem** Mapping in kanonische CSV normalisieren. XML-Rechnungen werden bislang nur erkannt/klassifiziert, nicht fachlich positionsweise übernommen. Kein produktiver Upload, keine vollständigen kundenspezifischen ERP-Formatprofile.
- Kein unabhängiger Nachweis für Vollständigkeit der Einkaufsperiode und der Vertragsnachträge. Die drei Pflichtflags und ERP-Kontrollsummen sind externe Angaben und niemals ein algorithmischer Nachweis. Der neue Gate-Status `READY_FOR_AUDIT` bestätigt ausschließlich Konsistenz mit übergebenen Kontrollen.
- **Verifizierte JWT-Subjektidentität ist implementiert, aber noch keine produktive IdP-Anmeldung.** DB-Grants und Widerruf sind vorhanden; externe Benutzeranlage/-sperrung, administratives Provisioning, JWKS-Rotation und Keyrotation fehlen. Der direkte lokale CLI-Testweg ist weiterhin ausdrücklich kein authentifizierter Kundendienst. Die HMAC-Signatur belegt nur, dass die Daten mit dem verwendeten Secret signiert wurden; kein gesetzlicher oder externer Identitätsnachweis. Die lokale CLI nimmt Tenant-/Gesellschaftskennung als Parameter und ist kein sicheres Kundentor.
- Ein **funktionaler OIDC-geschützter Browser-Arbeitsbereich mit Portal-BFF** ist im Repository vorhanden und synthetisch getestet; aber **kein** produktiv konfigurierter Identity Provider, echter Kundenvertrag, vom VPS erreichbarer Produktivservice, echter ClamAV-Betrieb oder freigegebener öffentlicher Multi-Tenant-Upload. Browser-Pilot mit realen Kunden ist nicht abgenommen.
- Keine Live-Lexware-/weclapp-/Odoo-/Frappe-/Dolibarr-Schnittstellen, keine Marktplatzfreigabe.
- Manuelle Vertragsregel-Freigabe über das Arbeitsbereich-Formular ist vorhanden; **keine** durchgehend versionierte EXTRACTED/NEEDS_CONFIRMATION/APPROVED/SUPERSEDED-Regelzustandsmaschine. Die eigenständig registrierte Mapping-HMAC-Freigabe besteht im HTTP-Upload/Bundle-Pfad, nicht im lokalen, operatorgesteuerten Legacy-CLI. Keine automatische rechtliche Bewertung und keine juristische Forderungsdurchsetzung.
- RecoveryLedger mit MariaDB, Belegmeldungen, unabhängiger manueller Finanzverifikation und 3%-Honorar**vorschlag** ist vorhanden. **Noch keine** verbindliche Fee-Allocation, steuerliche Prüfung, Rechnungsgenehmigung oder automatische Rechnungsstellung; billable_recovery_net und fee_due_net bleiben bis zu dieser Freigabe absichtlich 0.00.
- Keine abgesicherte Ausführung untrusted PDF, keine produktive DSGVO-/RDG-/Lizenzprüfung oder Kundenabnahme.
- Die endgültige Veröffentlichungs-/Distributionslizenz ist eine noch offene Eigentümerentscheidung.

## Lokale Verifikation

Python >=3.11:

~~~bash
python -m pip install -e ".[import,registry,auth,universal,api]"
python -m unittest discover -s tests -v
python -m compileall -q src tests
python -m lowhangingfruitme.cli tests/fixtures/flat_rebate.json

lhfm audit-csv --rule tests/fixtures/rule.json \
  --transactions tests/fixtures/transactions.csv \
  --settlements tests/fixtures/settlements.csv \
  --source-system sample-erp \
  --controls tests/fixtures/source_controls.json \
  --approval /tmp/lhfm-approval.json \
  --contract-source tests/fixtures/synthetic_agreement.txt \
  --tenant-id T-SYN-1 \
  --legal-entity-id LE-SYN-1 \
  --confirm-transactions-complete \
  --confirm-settlements-complete \
  --confirm-agreements-complete
~~~

Vor dem CSV-Beispiel müssen MariaDB und ein nur für Tests zugelassener Registry-Datenbanknutzer bereitstehen; `tests/scripts/setup_approval_registry.py` darf ausschließlich auf `lhfm_test` laufen. Danach muss das **synthetische** Test-Rezept aus dem [README](../README.md) den Zufallsschlüssel und den signierten Testbeleg erzeugen. Ohne diese Vorarbeit läuft die Freigabe aus Sicherheitsgründen nicht.

Für PDF: optional `python -m pip install -e ".[docs]"`, dann `lhfm extract-pdf --file <lokaler-pfad.pdf>`. Nicht als freigegebenes Kunden-Upload-Interface einsetzen.

## Nächster produktbezogener Schritt

Reale synthetisch nachgebildete Exportvarianten je ERP und XRechnung/ZUGFeRD fachlich gegen das kanonische Modell benchmarken; CI und sichere Dateiverarbeitung ausbauen. Echte anonymisierte und rechtmäßig bereitgestellte Testdokumente mit manuellem Goldstandard gegen Docling und den Rechenkern prüfen; Spaltenmapping und fehlende Buchungsdaten definieren. Die vorhandene stagingfähige API und das Portal mit echtem IdP, vollständig geprüftem Dateibetrieb, externen Vertragsbedingungen und Pilotabnahme absichern und produktiv installieren. Keine ungestützten Release- oder Return-on-Investment-Aussagen.

**Abnahme gegen den verbindlichen Vier-Wochen-Plan:** [FOUR_WEEK_ACCEPTANCE.md](FOUR_WEEK_ACCEPTANCE.md). **Reproduzierbarer synthetischer Goldstandard:** [PILOT_GOLDSTANDARD.md](PILOT_GOLDSTANDARD.md).

## v0.14-Workstream – aktuelle Vertragsrevision (noch kein abgenommener Release)

Umgesetzt im **Entwicklungscode**: SQL 008 ergänzt Revisionsmetadaten, einen eindeutigen aktuellen Regelkopf je Tenant/Gesellschaft/Vertrag/Regel, append-only APPROVED/SUPERSEDED/REVOKED-Ereignisse sowie transaktional geschützte Registrierung und Audit-Gates. Alte signierte Genehmigungen werden beim Nachtrags-Approval als superseded markiert und für neue Audits gesperrt. Historische abgeschlossene Berichte bleiben unverändert gespeichert. Das Upgrade erfordert eine kontrollierte Migration; bestehende Genehmigungsdatensätze mit nicht befüllten Revisionsfeldern werden **nicht** automatisch als aktuelle Revision vertraut. Die autorisierte Vorlage neuer HMAC-Receipts bleibt ausdrücklich manuell und extern authentifiziert.

**Weiter offen:** Statusstufen EXTRACTED und NEEDS_CONFIRMATION als eigener an Vertragsdokumente gekoppelter, sicherer Draft-/Review-Lifecycle; echte aus Docling stammende fundstellenbezogene Änderungsprüfung; produktiver Migrationsnachweis, unabhängiger fachlicher Pilot. Bis zum entsprechenden CI-Nachweis keine Behauptung, v0.14 sei insgesamt fertig.
