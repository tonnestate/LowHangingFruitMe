![LowHangingFruitMe – Neon-Banner](docs/Neon-Low-Hanging-FruitMe-Banner.png)

# LowHangingFruitMe

**B2B Revenue Recovery for FruitStack.** Ein eigenständiger, beleggestützter Prüfdienst für nicht vollständig realisierte Lieferantenboni und vertraglich eindeutige Einkaufskonditionen.

**Version:** 0.6.0 (OIDC-Access-Token-Prüfung und Freigabe-Service, Entwicklung)  
**Status:** ausführbare Bonusengine und lokale CSV-/PDF-Adapter; **kein** Kundenportal, keine Live-ERP-Anbindung, keine rechtliche Forderungseinziehung und keine produktiv validierte Rückgewinnung.

## Was funktioniert

- Deterministische Berechnung von Jahresboni, rückwirkenden und marginalen Staffeln sowie festen Schwellenprämien; Dezimalarithmetik, Retouren, Gutschriften, Stornierungen und eindeutige Vertragsperioden.
- Einlieferung kanonischer Einkaufs- und Gutschriften-CSV mit **Frictionless** als echtem Schema-Prüfer und anschließend strenger fachlicher Validierung; Herkunftsverweise auf Datei-Hash und Quellzeile.
- **Freigabenachweis:** Vertragsregel und konkrete Dokumentdatei werden per SHA-256 mit einer HMAC-signierten Bestätigung verknüpft. Der CSV-Pfad verlangt Mandanten- und Gesellschaftsbindung; `approved: true` allein genügt nicht. Keine produktive Prüfer-Authentifizierung oder Widerrufsverwaltung.
- **Verifizierte Access-Tokens:** RFC-9068-kompatible RS256-Signaturprüfung anhand einer vertrauenswürdig bereitgestellten öffentlichen JWKS, Prüfung von Aussteller, Audience, Client-ID, Gültigkeit und Berechtigungsumfang. Eine durch MariaDB berechtigte Person kann Regeln über `AuthenticatedApprovalService` freigeben, widerrufen und eingeschränkte Audits starten. **Noch keine Live-IdP-Anbindung oder öffentliche API.**
- **Persistierte Freigaben:** Genehmigungen werden in MariaDB registriert, mandantenbezogen freigegeben oder widerrufen und während der Berechnung durch `SELECT ... FOR UPDATE` vor konkurrierenden Änderungen geschützt. Ohne Registry läuft kein finaler CSV-Audit.
- **Readiness-Gate:** separate ERP-Kontrollsummen für Anzahl und Nettobetrag, Scope-Kontrolle für Lieferant/Vertrag/Periode, Status `READY_FOR_AUDIT` / `LIMITED` / `NOT_READY`. Bei fehlenden oder widersprüchlichen Kontrollen entsteht kein abschließender Geldbefund.
- Lokale PDF-Extraktion über **Docling** in belegbare Segmente (Text/Tabellen, Seite, Hash), ausdrücklich **ohne automatische Vertragsregel-Freigabe**.
- Wiederholbare synthetische Regressionstests, GitHub Actions für Python 3.11/3.12, getrennte Entwicklungs- und Betriebsgrenzen.
- Jeder Bericht trennt rechnerische Differenz, unsichere Datenlage und tatsächlich realisierte sowie abrechenbare Erfolge.

## Installation und reproduzierbarer lokaler Test

Python >= 3.11; die reine Rechenengine benötigt keine externen Runtime-Abhängigkeiten.

~~~bash
python -m pip install -e ".[import,registry,auth]"
python -m unittest discover -s tests -v
python -m lowhangingfruitme.cli tests/fixtures/flat_rebate.json
~~~

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
- [Signierte Regel-Freigaben und ihre Grenzen](docs/RULE_APPROVAL.md)
- [MariaDB-Freigaberegister, Widerruf und transaktionale Sperre](docs/APPROVAL_REGISTRY.md)
- [Authentifizierung und JWT-Trust-Boundaries](docs/AUTHENTICATION.md)
- [Release-Evidenz](EVIDENCE.md), [Changelog](CHANGELOG.md), [Sicherheit](SECURITY.md), [Agentenvorgaben](AGENTS.md), [Drittherstellerhinweise](THIRD_PARTY_NOTICES.md)

Das öffentliche Repo enthält ausschließlich eigene Implementierung und synthetische Testdaten. Es wurden keine Fremd-ERP-Quelltexte kopiert. Für das Projekt wurde noch **keine Open-Source-Distributionslizenz festgelegt**; öffentlich lesbarer Code ist nicht automatisch frei zur Weiterverwendung.
