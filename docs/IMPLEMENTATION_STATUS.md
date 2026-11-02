# Implementation status – LowHangingFruitMe v0.2.0

**Stand:** 02.11.2026. Produktentwicklung, kein kommerzieller oder produktiver Betrieb. Der aktuelle Revisionsnachweis steht in [EVIDENCE.md](../EVIDENCE.md); keine behaupteten Live-Kunden- oder ERP-Erfolge.

## Implementiert

**Deterministische Bonusengine 0.1.0:** Regelarten FLAT_RATE, RETROACTIVE_FULL_BASE, MARGINAL_PER_TIER und FIXED_THRESHOLD_REWARD; Decimal-Rechnung; Retouren, Gutschriften und Rückbuchungen; Lieferanten-/Perioden-/Währungsprüfung; separate Review-/Fehlerzustände; reproduzierbarer Snapshot-Hash. Der Report behauptet weder juristisch gültige Forderungen noch abrechenbare Erlöse.

**CSV-Import v0.2.0:** Strikte kanonische Header für Einkaufstransaktionen und Gutschriften, Validierung mit Frictionless plus Domain-Parser, Dateisignatur-SHA256/Zeilenfundstellen, keine automatischen Schema- oder Zahlenkorrekturen, Duplicate-ID-Ablehnung, lokale End-to-End-CLI zur bestehenden Engine.

**PDF-Extraktionsadapter v0.2.0:** Lokale PDF-Annahme mit einfachen Dateisignatur-/Größenkontrollen, Docling-Dokumentkonvertierung und Quellenverweisen auf Datei-Hash, Segment und Seite. Das Ergebnis ist stets NEEDS_HUMAN_REVIEW; kein Extraktionsresultat erzeugt eigenmächtig eine freigegebene Bonusregel.

**Repository:** installierbares Python-Paket, getrennte optionale Abhängigkeiten, GitHub Actions Matrix, synthetische Testdateien, AGENTS.md, SECURITY.md, CHANGELOG.md, EVIDENCE.md, THIRD_PARTY_NOTICES.md und ausführliche Konzept- und Donor-Dokumentation.

## Ungeprüfte Aspekte und klare Grenzen

- GitHub Actions ist der tatsächliche Testnachweis; nicht jede neu geschriebene Testdatei wurde lokal ausgeführt. Ergebnisse mit Run-ID in EVIDENCE.md festhalten.
- Docling wurde noch nicht anhand echter annotierter Vertragsdokumente in einer isolierten Produktionsumgebung benchmarkgetestet. Docling selbst ist noch kein Beleg für ein vollständig funktionierendes Dokumentenprodukt.
- Kein XLSX-/XML-Importer oder kundenspezifisches Spaltenmapping; Eingaben müssen aktuell das veröffentlichte kanonische CSV-Schema erfüllen.
- Kein unabhängiger Nachweis für Vollständigkeit der Einkaufsperiode und der Vertragsnachträge. Die drei Pflichtflags sind externe Angaben und niemals ein algorithmischer Nachweis.
- Kein Tenant-Login, Kundenportal, öffentlicher API-Service, Vertragsannahme, gesicherter Upload, Kundenspeicherung oder Download-Workflow.
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
  --confirm-transactions-complete \
  --confirm-settlements-complete \
  --confirm-agreements-complete
~~~

Für PDF: optional `python -m pip install -e ".[docs]"`, dann `lhfm extract-pdf --file <lokaler-pfad.pdf>`. Nicht als freigegebenes Kunden-Upload-Interface einsetzen.

## Nächster produktbezogener Schritt

Echte anonymisierte und rechtmäßig bereitgestellte Testdokumente mit manuellem Goldstandard gegen Docling und den Rechenkern prüfen; Spaltenmapping und fehlende Buchungsdaten definieren. Danach eine sichere, mandantenfähige API mit Kundenportal und bestätigten Vertragsbedingungen. Keine ungestützten Release- oder Return-on-Investment-Aussagen.
