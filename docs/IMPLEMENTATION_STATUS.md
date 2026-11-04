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

**Weiter offen:** Statusstufen EXTRACTED und NEEDS_CONFIRMATION als eigener an Vertragsdokumente gekoppelter, sicherer Draft-/Review-Lifecycle; echte aus Docling stammende fundstellenbezogene Änderungsprüfung; produktiver Migrationsnachweis, unabhängiger fachlicher Pilot. Einzel-Abnahme des Head-/Supersession-Pfads: **PASS in synthetischer MariaDB-CI** (310 Python-Tests je Version 3.11/3.12, Actions 41697334882). Die vollständige v0.14-Freigabe einschließlich Vorschlags-Lifecycle und realer Vertrags-/Kundenprüfung bleibt **OFFEN**.


## Nachtrag: SQL-Schema-Startgate (synthetische CI-Abnahme bestanden)

`lhfm-schema-check` und `require_operational_schema` prüfen die tatsächlich
benötigten MariaDB-Strukturen aus SQL 001–008 rein lesend. Die FastAPI-Factory
verweigert bei Drift/fehlender Migration den Start. Negative Unit-Tests decken
fehlende 007/008-Felder und -Tabellen, fehlende Constraints, ungeeignete
Tabellenengine und den falschen 3%-Default ab; ein echter isolierter MariaDB-
Integrationstest ist im CI-Suite enthalten. **Nachgewiesen:** GitHub Actions [41826517951](https://github.com/tonnestate/LowHangingFruitMe/actions/runs/41826517951), Commit `6300564787c623e6eed3779e581de39ad70670fe`, 319 Python-Tests je Runner (3.11 und 3.12), einschließlich isolierter echter MariaDB und negativer Schema-Gates; beide Jobs erfolgreich. Noch **kein** eigenständiger SQL-Runner,
keine automatischen oder produktiven Migrationen; erforderliche v0.14-
Bestandsfreigaben bleiben offen.


### v0.14-Deadlock-Prävention (04.11.2026 – CI bestanden)

Widerruf übernimmt jetzt dieselbe Reihenfolge von InnoDB-Row-Locks wie Audit-Guard und signierte Supersession (Head → Approval → Reviewer). Der neue CI-MariaDB-Test hält ausschließlich den Head-Lock und kontrolliert, dass Revoke nicht vorzeitig committen kann. **CI bestanden:** [Actions 41827901269](https://github.com/tonnestate/LowHangingFruitMe/actions/runs/41827901269), Python 3.11/3.12; ohne produktive Konkurrenzlastabnahme.


### Revisionssichere SQL-Migrationshistorie (04.11.2026 – synthetische CI bestanden)

Der neue CLI-Befehl `lhfm-migrate` ist unabhängig vom API-Start. Er unterstützt schreibfreien Plan, operatorbestätigte DDL-Installation, SHA256-Checksums, MariaDB Advisory Lock und vor DDL persistierte IN_PROGRESS-Marker. API-Start validiert jetzt auch die lückenlose Versionierung 001–008. CI-Setup nutzt denselben Runner auf leerer Testdatenbank. **CI bestanden:** [Actions 41828849927](https://github.com/tonnestate/LowHangingFruitMe/actions/runs/41828849927): 330 Python-Tests je Version 3.11/3.12, inklusive frisch angewandter 001–008-Migrationen, Ledger-No-Op-Test und Schema-Gate. Echte Bestandsmigration, Wiederherstellungstest, Livebetrieb und kundenbezogene Vertrags-/Honorarfreigaben sind weiterhin offen.


### Betriebs-Readiness statt bloßer HTTP-Liveness (04.11.2026 – synthetische CI bestanden)

Neben unverändertem `GET /healthz` (Prozess lebt) wurde `GET /readyz` eingeführt. Ready ist nur möglich, wenn Upload-, Bundle- und Recoverydienste konfiguriert sind, der MariaDB-Schema-/Migrations-Ledger-Preflight besteht und ein echter `ClamAVScanner` am lokalen UNIX-Socket auf `zPING` mit `PONG` reagiert. Test-Stubs signalisieren keine Produktionsbereitschaft. Fehler werden als unspezifisches 503 (`NOT_READY`) ausgegeben, nicht mit DB- oder Hostdetails. **CI bestanden:** [Actions 41829742266](https://github.com/tonnestate/LowHangingFruitMe/actions/runs/41829742266): 336 Tests je Python 3.11 und 3.12 einschließlich ClamAV-PING-Positiv/Negativ und `/readyz` bei Dienst-/Socket-Ausfall. Ein erfolgreicher Test mit einem simulierten Socket ist **kein** Live-Scanner-Nachweis.


### RS256-JWKS-Schlüsselwechsel ohne Dienstneustart (04.11.2026 – synthetische CI bestanden)

Die geprüfte lokale JWKS-Datei wird bei jeder API-Tokenprüfung anhand SHA-256 neu validiert, bei Änderungen atomar ersetzt und bei ungültiger Datei fail-closed behandelt. Tests für Key-Rotation, alten KID, defekte JWKS-Datei und Wiederherstellung sind ergänzt und [Actions 41830627024](https://github.com/tonnestate/LowHangingFruitMe/actions/runs/41830627024) bestand mit 338 Tests unter Python 3.11/3.12. Die parallele Dateisnapshot-Race wurde durch eine einzige Lock-geschützte Lese-/Validierungs-/Swap-Sequenz behoben. Dies ist kein Live-IdP, keine Provider-Discovery, keine Session-Erneuerung und keine Rotation des HMAC-Vertragsfreigabeschlüssels.


### SQL-Migrations-Prüfsummen gegen Release-Baseline (04.11.2026 – CI bestanden)

Die API prüft für die Migrationen 001–008 nun gegen fest im Anwendungscode verankerte SHA256-Release-Prüfsummen (nicht nur das 64-stellige Format), und der Wartungs-Runner verweigert veränderte historische SQL-Dateien schon vor DDL. Ergänzte Negativtests für manipulierte Ledger-Zeilen und SQL-Dateien. **CI bestanden:** [Actions 41832270878](https://github.com/tonnestate/LowHangingFruitMe/actions/runs/41832270878) mit 339 Python-Tests je 3.11/3.12. Reale Bestandsmigration und produktive Upgrade-Abnahme sind getrennt.


### v0.14 dokumentengebundener Regelkandidat (04.11.2026 – synthetische CI bestanden)

Neues SQL 009 mit `lhfm_contract_candidates` und append-only Ereignissen, API für Kandidatenextraktion, Lesezugriff und Human-Review, synchronisierter SQL-009-Schema-/Prüfsummencheck, HTML-Kundenprozess mit ausdrücklich gewählter PDF-Fundstelle und im Regelfall zwingender Kandidatenbindung beim Erstellen des signierten Bundles. Die DB-Revisionstransaktion schreibt in derselben Transaktion `APPROVED` und propagiert `SUPERSEDED`/`REVOKED`. Für bestehende synthetische Tests bleibt `require_candidate=False` explizit gesetzt. Noch **kein** Nachweis von echtem OCR-/Docling-Parsing auf dem Zielhost, Modellassets, Netzsperre, rechtlichem Vertragsbezug, realem Anbieterlogin oder öffentlicher Releasefähigkeit. **Abgenommen in isolierter CI:** [Python Actions 41835718850](https://github.com/tonnestate/LowHangingFruitMe/actions/runs/41835718850) mit 351/351 Tests auf Python 3.11 und 3.12 nach Behebung der 409/422-Fehlerklassifikation, [Portal Actions 41834409466](https://github.com/tonnestate/LowHangingFruitMe/actions/runs/41834409466) mit erfolgreichem Build, Typecheck und Playwright-Browserprüfung. Echte PDF-/IdP-/VPS-/Rechtsabnahme weiterhin offen.


### Docling-Subprozess-Härtung (04.11.2026 – synthetische CI bestanden)

Der dokumentenverarbeitende Unterprozess wurde auf inkrementell begrenzten stdout (1 MiB), 120-Sekunden-Abbruch mit Prozessgruppen-Kill, Worker-eigene Ressourcenlimits und zwingende root-kontrollierte Betriebssystem-Sandbox umgestellt. Die lokale Netzwerk-Namespace-Probe ist unter `lhfm-docling-check` und bei `/readyz` integriert; ohne konfigurierten sicheren Launcher verweigert die Parserstrecke jede Extraktion. **CI bestanden:** [GitHub Actions 41841304792](https://github.com/tonnestate/LowHangingFruitMe/actions/runs/41841304792), **360 Tests unter Python 3.11 und 360 unter Python 3.12**. Die CI nutzt ausschließlich synthetische CLI-Unterprozesse, keine echten Docling-PDF-Konvertierungen und keinen nachgewiesenen VPS.


### OIDC-Refresh und Browser-Session (04.11.2026 – synthetische Portal-CI bestanden)

Im BFF implementiert: gleichursprünglich gepinnter HTTPS-Token-Endpoint, Client-Credentials-Refresh mit Timeout und 16-KiB-Limit, prozesslokales Singleflight, erfolgreiche Access-/Refresh-Rotation mit Auth.js-JWE-Encode und Auth.js-kompatibler Cookie-Bereinigung; Fehler führt zur erneuten Anmeldung ohne Credentials an den Browser. **CI bestanden:** [Actions 41842914601](https://github.com/tonnestate/LowHangingFruitMe/actions/runs/41842914601), 16 Node-Unit-Tests, Next.js-Build, TypeScript und Playwright erfolgreich. Keine reale IdP-/MFA-/Multi-Worker-/VPS-Abnahme.


### v0.15 – Billing-Handoff statt theoretischer Honorarrechnung (04.11.2026 – synthetische CI bestanden)

Neue SQL-010-Tabellen `lhfm_commercial_terms`, `lhfm_billing_grants`,
`lhfm_billing_packets` und Append-only-Ereignisse. Auf aktive
Kundenannahme-/Legal-Prüf-Referenzen aus der separat verwalteten
Datenbank gebundene Zweipersonenfreigabe, erneut gesperrter
Recovery-Stand beim endgültigen Handoff, historische 3%/neue 5%,
Stale-/Reversal-/Correction-Prüfung und abgegrenzte BFF-Routen.
**CI bestanden:** [Actions 41850007747](https://github.com/tonnestate/LowHangingFruitMe/actions/runs/41850007747), 424/424 Python-Tests auf 3.11 und 3.12. Zusätzlich [Portal Actions 41848399198](https://github.com/tonnestate/LowHangingFruitMe/actions/runs/41848399198), Build/Typecheck/Browser erfolgreich. Tests schließen Vertragsrevision, Entzug der kommerziellen Freigabe, unterschiedliche Vertragsraten, unabhängige Zweitfreigabe, Reversal, Void und falsche Mandanten ein;
**eine produktive Rechnung, Bankverifikation und externe Rechtsfreigabe
sind NICHT nachgewiesen**.


### v0.16 – signiertes verschlüsseltes Disaster Recovery (04.11.2026 – synthetische CI bestanden)

Der dedizierte Befehl `lhfm-dr` erstellt während bestätigter
Schreibstillstandsphase einen age-verschlüsselten MariaDB-Dump und zwei
age-verschlüsselte Archive aller privaten Audit-/Upload-Dateien. Das
verschlüsselte Manifest enthält Datenbanktabellen-Zeilenanzahlen und
Dateihashes und ist Ed25519-signiert; der Prüfprozess verlangt
unabhängig bereitgestellte Verifikationsschlüssel. Die
Wiederherstellung schreibt nur in eine vorab erzeugte leere
`lhfm_restore_*`-DB und optionale isolierte private Verzeichnisse.
Kein unverschlüsselter Dump auf Festplatte, keine automatische
Produktivrestaurierung. Operativer VPS-Test und unabhängige RPO-/RTO-
Abnahme fehlen weiterhin.


Die isolierte DR-Abnahme ist über [Actions 41855424879](https://github.com/tonnestate/LowHangingFruitMe/actions/runs/41855424879) mit tatsächlichem MariaDB-11.4-Dump/Import, age-Verschlüsselung, Ed25519-Signatur, Leer-Datenbank-Gate, privatem Original-Dateivergleich und Ablehnung von Replay/Fälschung **erfolgreich**. Die [Python-Gesamtsuite 41855296597](https://github.com/tonnestate/LowHangingFruitMe/actions/runs/41855296597) ist unter 3.11/3.12 mit je **430 bestandenen Tests** erfolgreich. Keine produktiven Kundenfiles oder VPS-Restore wurden verwendet.


Die abschließende DR-Härtung erzwingt physisch getrennte Upload-/
Audit-Quellbäume und hält MariaDB-Credentials, Ed25519-Signaturschlüssel,
Verifikationsschlüssel sowie age-Identität aus Snapshot- bzw.
Backup-Verzeichnissen heraus. Ein zusätzlicher Negativtest schützt
diese Grenze. Bestehende Betriebs-Gates bleiben offen.
