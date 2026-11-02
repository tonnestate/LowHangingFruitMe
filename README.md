# LowHangingFruitMe

**B2B Revenue Recovery for FruitStack.** Ein eigenständiger, beleggestützter Prüfdienst für nicht vollständig realisierte Lieferantenboni und vertraglich eindeutige Einkaufskonditionen.

**Version:** 0.3.0 (Data-Readiness-Gate, Entwicklung)  
**Status:** ausführbare Bonusengine und lokale CSV-/PDF-Adapter; **kein** Kundenportal, keine Live-ERP-Anbindung, keine rechtliche Forderungseinziehung und keine produktiv validierte Rückgewinnung.

## Was funktioniert

- Deterministische Berechnung von Jahresboni, rückwirkenden und marginalen Staffeln sowie festen Schwellenprämien; Dezimalarithmetik, Retouren, Gutschriften, Stornierungen und eindeutige Vertragsperioden.
- Einlieferung kanonischer Einkaufs- und Gutschriften-CSV mit **Frictionless** als echtem Schema-Prüfer und anschließend strenger fachlicher Validierung; Herkunftsverweise auf Datei-Hash und Quellzeile.
- **Readiness-Gate:** separate ERP-Kontrollsummen für Anzahl und Nettobetrag, Scope-Kontrolle für Lieferant/Vertrag/Periode, Status `READY_FOR_AUDIT` / `LIMITED` / `NOT_READY`. Bei fehlenden oder widersprüchlichen Kontrollen entsteht kein abschließender Geldbefund.
- Lokale PDF-Extraktion über **Docling** in belegbare Segmente (Text/Tabellen, Seite, Hash), ausdrücklich **ohne automatische Vertragsregel-Freigabe**.
- Wiederholbare synthetische Regressionstests, GitHub Actions für Python 3.11/3.12, getrennte Entwicklungs- und Betriebsgrenzen.
- Jeder Bericht trennt rechnerische Differenz, unsichere Datenlage und tatsächlich realisierte sowie abrechenbare Erfolge.

## Installation und reproduzierbarer lokaler Test

Python >= 3.11; die reine Rechenengine benötigt keine externen Runtime-Abhängigkeiten.

~~~bash
python -m pip install -e ".[import]"
python -m unittest discover -s tests -v
python -m lowhangingfruitme.cli tests/fixtures/flat_rebate.json
~~~

CSV-End-to-End-Prüfung mit **synthetischen** Dateien:

~~~bash
lhfm audit-csv \
  --rule tests/fixtures/rule.json \
  --transactions tests/fixtures/transactions.csv \
  --settlements tests/fixtures/settlements.csv \
  --source-system sample-erp \
  --controls tests/fixtures/source_controls.json \
  --confirm-transactions-complete \
  --confirm-settlements-complete \
  --confirm-agreements-complete
~~~

Die drei Bestätigungen sowie die Kontrollsummen sind **explizite externe Angaben** und kein unabhängiger ERP-Vollständigkeitsbeweis. Ohne Kontrollsummen gibt die CSV-CLI lediglich eine Readiness-Diagnose aus und erzeugt keinen berechneten Differenzfall. Ohne diese Bestätigungen liefert der Audit lediglich einen Prüfstatus mit Einschränkungen. Bei vollständig bestätigtem synthetischem Beispiel: 200.000 EUR anrechenbarer Nettobezug, 2 % Bonus, 1.500 EUR Gutschrift → 2.500 EUR **rechnerische Differenz**, 0 EUR automatisch abrechenbares Erfolgshonorar.

Docling separat installieren und lokal ein PDF unter Vorbehalt der Sicherheitsbedingungen prüfen:

~~~bash
python -m pip install -e ".[docs]"
lhfm extract-pdf --file /path/to/your/local-contract.pdf
~~~

**Achtung:** Der Docling-Adapter ist ein lokaler Prototyp ohne isolierten Upload-Worker, echte OCR-Qualitätsabnahme oder garantierte Offline-Modellbereitstellung. Keine Kundendokumente vor Prüfung des Host-Sicherheitskonzepts verarbeiten.

## Produktarchitektur

Kundenportal / Upload / ERP-Connector / REST-API (**geplant**) → Intake-Adapter (CSV-Frictionless/PDF-Docling) → bestätigte Vertragsregel → deterministischer Audit → belegte Differenzakte → Recovery-Ledger und erfolgsabhängige Abrechnung (**geplant**).

Es wird **kein** eigenständiges ERP oder FruitStack-Orchestrierungssystem dupliziert. Kernberechnung und Datenimport sind plattformunabhängig. Lexware, weclapp, Odoo, ERPNext/Frappe, Dolibarr und Oro sind recherchierte Integrations-/Distributionsziele; sie sind **nicht produktiv angebunden**.

## Geschäft und Grenzen

Angedachtes Kundenangebot: eine einmalige Prüfung gegen **10 % von der nachweislich, zurechenbar und wirtschaftlich tatsächlich realisierten zusätzlichen Nettovergütung**. Erfolgshonorar, RDG-Abgrenzung, Datenschutz und Vertragstexte sind vor kommerziellem Start extern rechtlich zu prüfen. Das Produkt betreibt im ersten Umfang weder Inkasso noch autonomes Forderungsmanagement.

## Dokumentation

- [Fach- und Architekturkonzept](docs/CONCEPT.md)
- [Donorenregister und Lizenzgrenzen](docs/DONORS.md)
- [Kanonischer Datenvertrag und API-Spezifikation](docs/API_AND_DATA.md)
- [Vertrags- und Vergütungsmodell](docs/LEGAL_AND_REVENUE.md)
- [Lieferplan und Abnahmekriterien](docs/DELIVERY_PLAN.md)
- [Tatsächlicher Implementierungsstand](docs/IMPLEMENTATION_STATUS.md)
- [Prüfkriterien und Kontrollsummen für Data Readiness](docs/DATA_READINESS.md)
- [Release-Evidenz](EVIDENCE.md), [Changelog](CHANGELOG.md), [Sicherheit](SECURITY.md), [Agentenvorgaben](AGENTS.md), [Drittherstellerhinweise](THIRD_PARTY_NOTICES.md)

Das öffentliche Repo enthält ausschließlich eigene Implementierung und synthetische Testdaten. Es wurden keine Fremd-ERP-Quelltexte kopiert. Für das Projekt wurde noch **keine Open-Source-Distributionslizenz festgelegt**; öffentlich lesbarer Code ist nicht automatisch frei zur Weiterverwendung.
