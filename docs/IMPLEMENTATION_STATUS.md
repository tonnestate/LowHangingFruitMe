# Implementation status – LowHangingFruitMe v0.7.0

**Stand:** 02.11.2026. Produktentwicklung, kein kommerzieller oder produktiver Betrieb. Der aktuelle Revisionsnachweis steht in [EVIDENCE.md](../EVIDENCE.md); keine behaupteten Live-Kunden- oder ERP-Erfolge.

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

**Öffentliche Website – eigener Stand `portal@0.1.0` (03.11.2026):** Deutsches Next.js-Frontend als isolierter Webdienst vorbereitet; Startseite, Lieferantenboni, Marge, O2C, Service, Preis/Ablauf, Eignungscheck, Bonusstaffeln, Bonusgutschriften, Wissensindex und fünf eigenständige Fachartikel. Originales Banner aus `docs/` ohne Bildkopie im Repository; Build-Pipeline erstellt unveränderte Bildkopie und CSS-Markenfarben anhand der tatsächlichen PNG-Pixel. Responsive Browser- und Interaktionstests 1440/768/390 bestanden, inklusive Navigations-, FAQ-, Rechner-, 404- und noindex/robots-Prüfungen. Neue Apache-/systemd-Konfigurationsvorlagen **nicht** auf den Produktivserver installiert. Die Portal-Website ist ein Marketing-Frontend, kein CRM, keine Auth-/Audit-API und keine Kundenanwendung. Aktuelle Rechtsseiten sind ausdrücklich Staging-Platzhalter. Vollständige Details: `docs/WEBSITE_STATUS.md`.

## Ungeprüfte Aspekte und klare Grenzen

- GitHub Actions ist der tatsächliche Testnachweis; nicht jede neu geschriebene Testdatei wurde lokal ausgeführt. Ergebnisse mit Run-ID in EVIDENCE.md festhalten.
- Docling wurde noch nicht anhand echter annotierter Vertragsdokumente in einer isolierten Produktionsumgebung benchmarkgetestet. Docling selbst ist noch kein Beleg für ein vollständig funktionierendes Dokumentenprodukt.
- XLSX und flexibel benannte CSV lassen sich mit **manuell bestätigtem** Mapping in kanonische CSV normalisieren. XML-Rechnungen werden bislang nur erkannt/klassifiziert, nicht fachlich positionsweise übernommen. Kein produktiver Upload, keine vollständigen kundenspezifischen ERP-Formatprofile.
- Kein unabhängiger Nachweis für Vollständigkeit der Einkaufsperiode und der Vertragsnachträge. Die drei Pflichtflags und ERP-Kontrollsummen sind externe Angaben und niemals ein algorithmischer Nachweis. Der neue Gate-Status `READY_FOR_AUDIT` bestätigt ausschließlich Konsistenz mit übergebenen Kontrollen.
- **Verifizierte JWT-Subjektidentität ist implementiert, aber noch keine produktive IdP-Anmeldung.** DB-Grants und Widerruf sind vorhanden; externe Benutzeranlage/-sperrung, administratives Provisioning, JWKS-Rotation und Keyrotation fehlen. Der direkte lokale CLI-Testweg ist weiterhin ausdrücklich kein authentifizierter Kundendienst. Die HMAC-Signatur belegt nur, dass die Daten mit dem verwendeten Secret signiert wurden; kein gesetzlicher oder externer Identitätsnachweis. Die lokale CLI nimmt Tenant-/Gesellschaftskennung als Parameter und ist kein sicheres Kundentor.
- Kein Tenant-Login, **kein funktionales Kundenportal** (Marketingportal ist nur für öffentliche Informationen gebaut), öffentlicher API-Service, Vertragsannahme, gesicherter Upload, Kundenspeicherung oder Download-Workflow.
- Keine Live-Lexware-/weclapp-/Odoo-/Frappe-/Dolibarr-Schnittstellen, keine Marktplatzfreigabe.
- Keine Regelinterpretations-/Freigabeoberfläche, keine automatische rechtliche Bewertung, keine juristische Forderungsdurchsetzung.
- Kein RecoveryLedger / Erfolgshonorar-Fee-Allocation / automatische Rechnungsstellung; billable_recovery_net und fee_due_net bleiben absichtlich 0.00.
- Keine abgesicherte Ausführung untrusted PDF, keine produktive DSGVO-/RDG-/Lizenzprüfung oder Kundenabnahme.
- Die endgültige Veröffentlichungs-/Distributionslizenz ist eine noch offene Eigentümerentscheidung.

## Lokale Verifikation

Python >=3.11:

~~~bash
python -m pip install -e ".[import]"
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

Reale synthetisch nachgebildete Exportvarianten je ERP und XRechnung/ZUGFeRD fachlich gegen das kanonische Modell benchmarken; CI und sichere Dateiverarbeitung ausbauen. Echte anonymisierte und rechtmäßig bereitgestellte Testdokumente mit manuellem Goldstandard gegen Docling und den Rechenkern prüfen; Spaltenmapping und fehlende Buchungsdaten definieren. Danach eine sichere, mandantenfähige API mit Kundenportal und bestätigten Vertragsbedingungen. Keine ungestützten Release- oder Return-on-Investment-Aussagen.
