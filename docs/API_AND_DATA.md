# LowHangingFruitMe – API-, Daten- und Rechenkern-Spezifikation v0.1

**Stand:** 03.11.2026 | **Status:** Zielvertrag **plus tatsächlich implementierte Teilbereiche bis v0.12.0**. JWT-geschützte Audit-API, Scannerpflicht-/Upload-Staging, signierte und fachlich bestätigte Datenpakete, Recovery-Ledger mit gesondertem Finanzprüfer sowie JSON-/PDF-/XLSX-Reportdownloads sind als synthetischer End-to-End-Pfad implementiert. Ein Next.js-OIDC-BFF ist im Code getestet, aber **weder reale Kundenanmeldung noch produktive ClamAV-/IdP-/VPS-Konfiguration** abgenommen. Keine Live-ERP-Anbindung, keine externe Pilotbestätigung, keine autorisierte tatsächliche Honorarrechnung. [Aktueller Abnahmestand](FOUR_WEEK_ACCEPTANCE.md) und [historische v0.8-Details](AUDIT_API.md).

## Aktuelle tatsächlich vorhandene HTTP-Routen (v0.12.0)

Zusätzlich zur untenstehenden **teilweise erst geplanten** API-Gesamtspezifikation existieren:

- `GET /healthz` – ohne Finanzdaten;
- `POST /v1/uploads`, `PUT /v1/uploads/{id}/content`, `GET /v1/uploads/{id}` – scannerpflichtiges, privates Staging;
- `GET /v1/uploads/{id}/inspect` – Quellspalten-/Arbeitsblattvorschläge;
- `GET /v1/uploads/{id}/invoice-preview` – schreibgeschützte UBL/CII-Vorschau, keine Buchung;
- `POST /v1/bundles` – ausdrücklich reviewed/signed Quellenpaket, nur beim berechtigten Prüfer;
- `POST /v1/audits`, `GET /v1/audits/{id}` – Freigabe- und Readiness-geschützte Prüfung;
- `GET /v1/audits/{id}/report.pdf`, `report.xlsx`, `report.json` – nur evidenzierter Audit, zusätzlicher Ledger-Lesescope und selber Mandant/Reviewer;
- `POST /v1/audits/{id}/recovery-events`, `GET /v1/audits/{id}/fee-ledger`, `POST /v1/recovery-events/{event_id}/review` – nachweisgebundene manuelle Realisierungen mit unabhängigem Finanzprüfer;
- `POST /v1/audits/{id}/case-status` – finanzprüferautorisierte Dispute-/Closure-/Reopen-Protokolle.

**Wichtig:** Keine der Routen bewirkt automatische ERP-Buchung, Lieferantenforderung, Bankzahlung, Rechnungsstellung oder tatsächliche 5%-Gebührenfälligkeit. Originaldokumente bleiben im privaten Staging und werden nicht über diese Download-Routen ausgespielt.

## 1. API-Grundregeln

Basisversion: /v1. Authentifizierung via serverseitiger Session im Portal bzw. scoped Tokens für Server-zu-Server; ERP-OAuth nur soweit durch jeweiligen Anbieter offiziell zugelassen. Jede Fachressource trägt tenant_id, legal_entity_id und bei Prüfaufträgen audit_id; der Client darf einen fremden Tenant durch Manipulation eines Parameters niemals erreichen.

Jede schreibende Request mit externer wirtschaftlicher Wirkung benötigt einen Idempotency-Key und eine Nachprüfung vorhandener Events. Alle Geldbeträge als Dezimalstrings in EUR oder explizit mit currency; keine binären Fließkommazahlen. Zeiten in ISO 8601 mit Zeitzonen; Abrechnungsperioden lokale Kalenderdaten ohne implizite UTC-Verschiebung. Fehler als maschinenlesbares code, message, field_errors, correlation_id. Pagination, Größen- und Rate-Limits sind Bestandteil des Kontrakts.

Alle Quellbelege werden im sicheren Speicher gehalten; API-Ergebnisse verwenden referenzierte, kurzlebig autorisierte Downloads statt dauerhafter öffentlicher URLs.

## 2. Endpunktvertrag

| Methode/Pfad | Zweck | Auth-/Sicherheit | Wichtiger Output |
|---|---|---|---|
| POST /v1/organizations | Unternehmens-Onboarding | verifizierter Betreiber | organization_id, Status |
| POST /v1/engagements | Mandat/Leistungsumfang festlegen | Org-Admin | engagement_id, Vertragsversion, effective_status |
| POST /v1/engagements/{id}/accept | Dokumentierte Annahme | Org-Admin + Auth-Nachweis | acceptance_id, terms_hash, timestamp |
| POST /v1/uploads | **v0.9 implementiert:** 15-Minuten-Absicht, Kategorie/Größe/SHA256, ohne öffentl. Slot | RS256-JWT lhfm:upload:write + aktiver Mandantenreviewer | upload_id, PENDING |
| PUT /v1/uploads/{id}/content | **v0.9 implementiert:** roher Datenstrom ≤16MiB; Hash, ClamAV-Socket-Prüfung und Dateityp | Gleiches JWT/DB-Recht; eigene UUID | CLEAN/REJECTED; keine Auditfreigabe |
| GET /v1/uploads/{id} | **v0.9 implementiert:** eigener Upload-Status, keine Bytes | Gleiches JWT/DB-Recht | status, sha256, usable_for_audit=false |
| POST /v1/uploads/{id}/finalize | **Noch nicht implementiert:** Übernahme in überprüften Dataset-/Vertragskontext | fachliche Freigabe erforderlich | keine öffentliche Funktion |
| POST /v1/agreements | Vereinbarungszuordnung anlegen | uploader | agreement_id |
| GET /v1/agreements/{id}/rules | Erkannte Klauseln und Quellen | reviewer | vorgeschlagene Regeln |
| POST /v1/agreements/{id}/rules/{rule_id}/approve | Regel mit Status/Fundstelle bestätigen | reviewer | rule_version, approved_at |
| POST /v1/datasets | Transaktions-/Gutschriften-Dataset anmelden | uploader | dataset_id, schema_version |
| GET /v1/datasets/{id}/quality | Import- und Mappingfehler | uploader/reviewer | coverage, errors, warnings |
| POST /v1/audits | **Teilweise implementiert v0.8**: synchrone Ausführung eines serverseitig vorregistrierten Bundles; keine öffentliche Upload-/Queue-Job-ID | JWT-Reviewer, DB Grant, UUID-Idempotenz | audit_id, status, audit_executed |
| GET /v1/audits/{id} | **Teilweise implementiert v0.8**: Bericht für genau den ausführenden Reviewer in gleicher Tenant-/Entity-Scope | JWT-Reviewer + DB-Grant | audit_id, status, audit_executed, report |
| GET /v1/audits/{id}/findings | Differenzakte | reviewer/viewer | cases + evidence links |
| GET /v1/audits/{id}/exports | Reportformate | freigegebene Rollen | PDF/XLSX/JSON-Manifeste |
| POST /v1/findings/{id}/recovery-events | belegte Realisierung/Storno | finance/reviewer | recovery_event_id, verified_status |
| GET /v1/engagements/{id}/fee-ledger | Vergütungsgrundlage | finance/operator | billable amount, fee estimate |
| POST /v1/billing-statements/{id}/approve | Rechnungsvorschlag freigeben | operator | invoice_reference (nach externem Fakturierungserfolg) |
| GET /v1/integrations | aktive Connectoren/Scopes | Org-Admin | integrations, data_permissions |
| DELETE /v1/integrations/{id} | Verbindung widerrufen | Org-Admin | revoked_at |

**Sicherheitskonzept:** Für den ersten Release dürfen Admin-Finanzaktionen zunächst über eine geschützte interne Oberfläche laufen. Ein API-Endpunkt darf niemals eine Rechnung erstellen oder eine externe Nachricht versenden, bloß weil ein LLM es vorschlägt.

## 3. Kanonisches Minimaldatenmodell

Keine unkontrollierte Kopie des ERP-Schemas. Relevante Entitäten mit fremden (source_system/source_record_id) und eigenen IDs:

- Organization(organization_id, name, country, registration_status)
- LegalEntity(legal_entity_id, organization_id, tax_entity_reference, currency, fiscal_year_start)
- UserAccess(user_id, organization_id, role, active)
- Engagement(engagement_id, legal_entity_id, scope, period, accepted_terms_version, acceptance_evidence, status)
- SourceSystem(source_system_id, type, credential_ref, read_scopes, last_sync_at)
- UploadedAsset(asset_id, tenant_id, sha256, media_type, size, storage_ref, retention_class, scan_state)
- Agreement(agreement_id, supplier_id, legal_entity_id, valid_from/to, document_refs)
- AgreementRevision(revision_id, amendment_chain, source_refs, effective_from/to, approval)
- BonusRule(rule_id, agreement_revision_id, rule_type, rate_table, base_definition, excludes, rounding, version, approval, source_span)
- Supplier(supplier_id, legal_entity_id, external_ids, verified_identity)
- ProductMapping(mapping_id, source_sku, normalized_sku, category, valid_from/to, approval)
- Transaction(txn_id, source_ref, supplier_id, transaction_type, transaction_date, booking_date, posted_status, item_ref, net_amount, currency, quantity, original_txn_id)
- Settlement(settlement_id, source_ref, supplier_id, agreement_ref, period, net_amount, currency, type, booking_status, economic_effect)
- DatasetVersion(dataset_id, source, version, hash, imported_rows, quality_summary, mapping_version)
- AuditRun(audit_id, engagement_id, input_snapshot_hash, rule_version_set, calculation_version, started_at, completed_at, status)
- Finding(finding_id, audit_id, rule_id, expected_amount, settled_amount, variance_amount, coverage_flag, evidence_refs, status)
- RecoveryEvent(recovery_id, finding_id, proof_ref, event_type, economic_effect_date, amount_net, adjudication_state, idempotency_key)
- FeeAllocation(fee_allocation_id, recovery_id, engagement_id, eligible_net, fee_pct, fee_amount, adjustment_of, invoice_id)
- AuditLog(event_id, actor, tenant_id, action, target, previous_hash, current_hash, timestamp)

**Speicherprinzip:** revisionssichere, versionierte Audit-Fakten in MariaDB; datenintensive Transaktionen/Snapshots in DuckDB/Parquet mit gesicherten Hashreferenzen und Verfügbarkeitsgarantien. Es gibt nur eine Definition der Geld-/Case-Zustände.

## 4. CSV/XLSX-Importkanon

P0 muss diese Spaltenbezeichnungen auf ein explizites Schema mappen können:

**Einkaufstransaktionen:** source_record_id, supplier_external_id, legal_entity_id, invoice_or_receipt_date, booking_date, posting_status, invoice_number, transaction_type, sku (optional für R1), quantity (optional für R1), eligible_net_amount, tax_amount (falls vorhanden), currency, reversal_ref (optional), warehouse_or_branch (optional).

**Gutschriften:** credit_note_id, supplier_external_id, accounting_date, agreement_reference/period, net_amount, currency, posted_flag, source_invoice_ref, offset_reference, reversed_flag, source_record_id.

**Verträge:** agreement_id, supplier_id, effective_from/to, settlement_period, rebate_type, eligible_base_definition, percentage/threshold schema, exclusions, amendment references, original_doc_ref, source_span and reviewer_approval.

Upload ist *nicht vollständig*, solange Lieferanten-ID/Name, Zeitraum, Nettobasis, Duplikate und Buchungsstatus nicht verifiziert sind. Fehlen für eine Staffel einzelne Monate, wird nur ein partieller, als nicht abschließend gekennzeichneter Check erlaubt.

## 5. Formeldefinitionen

Geldbeträge stets mit einer decimal-basierten, auf Währung und Vertrag ausgerichteten Rundung; die Regeln selbst werden versioniert.

**R1 (einfache Prozentregel):** eligibility_scope = Menge der unter Regeldefinition zulässigen gebuchten Basisgeschäftsvorfälle; eligible_base = Summe der zulässigen Nettobeträge nach Retouren/Storno und vertraglichen Ausschlüssen; expected_bonus = ROUND_BY_RULE(eligible_base × rate); recorded_bonus = Summe tatsächlich zuordenbarer, nicht stornierter und nach Vertragslogik anrechenbarer Settlements; variance = expected_bonus − recorded_bonus.

**R2 (Staffelregel):** drei ausdrücklich getrennte Semantiken: RETROACTIVE_FULL_BASE, MARGINAL_PER_TIER, FIXED_THRESHOLD_REWARD. Wenn das Vertragsdokument die Semantik nicht belegt oder der Reviewer sie nicht freigibt: NOT_CALCULABLE. Keine stillschweigende Annahme von „rückwirkend“ bei Schwelle.

**R3 (Produktgruppe):** eligible_base nur für gültige, genehmigte SKU/Warengruppen-Mappings und dokumentierte Stichtage; unbekannte Artikel ausweisen und keine plausible automatische Zuordnung als Fakt buchen.

**Kritische Differenzfälle:** Rechnungsdatum vs. Wareneingang; Periode vs. Geschäftsjahr; rückwirkender Vertragsnachtrag; Umsatzsteuer im Betrag; negative Gutschrift; Retouren außerhalb des Referenzzeitraums; Gutschriften für andere Jahre; konzern-/filialübergreifende Boni; überschreibende Vertragsklausel; mehrfache Gutschriften; Fremdwährung/FX-Regel.

## 6. Vollständigkeits- und Plausibilitätsgate

Ein Audit der Qualität COMPLETE ist nur möglich, wenn:
- alle vom Kunden benannten Verträge/Nachträge für den Zeitraum vorliegen,
- der vertragliche Berechnungsanker (Rechnung/Wareneingang/Umsatz) verfügbar ist,
- die Transaktionsdaten ein vollständiges, abgeglichenes Zeitfenster enthalten,
- Lieferanten und relevante Produktgruppen eindeutig zugeordnet wurden,
- Gutschriften/Verrechnungen samt Storno- und nachgelagerten Buchungen ausreichend erfasst sind,
- jede Regel genehmigt ist und nicht ausschließlich aus einem KI-Guess besteht,
- Summen- und Rollforward-Kontrollen keine ungeklärte Differenz zeigen.

Andernfalls ist ein BERICHT MIT EINSCHRÄNKUNG möglich, nie ein unqualifiziertes „0 EUR offen“ oder „100 % geprüft“.

## 7. Report- und Provenienzvertrag

Ein exportierter Report erhält ein Manifest:
- report_version, audit_run_id, input_manifest_hash, source_assets_sha256, rule_manifest_hash, parser_versions, model_version, calculation_engine_version;
- result_status, known_limitations, missing_sources, totals und source_exclusion_summary;
- pro Finding alle Belege, Seiten/Zellen/Transaktions-IDs und Zwischensummen;
- report_created_at, report_hash, authorizing_reviewer.

Eine Änderung an Daten, Klausel oder Berechnung erzeugt einen **neuen AuditRun**; der alte Report bleibt nachvollziehbar erhalten und wird als superseded gekennzeichnet. Es gibt keine heimliche Überschreibung bereits verteilter Befunde.

## 8. Security- und Tenant-Tests (harte Abnahme)

- Tenant A kann niemals Upload/Case/Report/Settlement von Tenant B lesen, auch nicht per erratenen IDs oder manipulierten File-Links.
- Fehlende Scopes auf ERP-Connector -> sicherer Abbruch und Datenlückenbericht, keine Rechteerweiterung.
- Upload von ausführbaren Dateien, Makrodateien, ZIP-Bomben und ungültigem MIME -> vor Verarbeitung abgelehnt.
- API-Limits schützen CPU/RAM/Dateigröße; große Auditjobs laufen begrenzt und können kontrolliert wieder aufgenommen werden.
- Doppelte Uploads und Replays erzeugen keine verdoppelten Transaktionen/Settlements/Rechnungen.
- Auth-/Vertragsannahme und Rechnungsvorschlag sind mit eindeutigem Actor und unveränderter Versionsreferenz verbunden.
- Ein in einem Dokument enthaltenes „ignoriere vorherige Anweisungen“ wird als untrusted content behandelt.

## 9. Reproduzierbare Akzeptanzbeispiele

**F01:** 200.000,00 EUR eligible base, 2 % R1, 1.500,00 EUR zugeordnete erhaltene Bonusgutschrift -> erwarteter Bonus 4.000,00 EUR, Differenz 2.500,00 EUR. Nur wenn Zeitraum, Gutschrift und Basis vollständig sind: EVIDENCED.

**F02:** 100.000,00 EUR Umsatz, 2 % ab Schwelle 80.000,00 EUR: ohne Staffelsemantik -> NOT_CALCULABLE. Mit RETROACTIVE_FULL_BASE -> 2.000,00 EUR; mit MARGINAL_PER_TIER -> 400,00 EUR, sofern alle anderen Vertragsannahmen gleich sind.

**F03:** Korrektur/Storno von 500,00 EUR zur ursprünglich realisierten 2.000,00-EUR-Gutschrift -> Netto-Realisierung 1.500,00 EUR; Fee-Allocation muss genau einmal um 25,00 EUR (5 % von 500,00 EUR) korrigiert werden.

**F04:** Zwei gleichlautende Lieferanten-Firmennamen mit unterschiedlichen verifizierten Kennungen dürfen selbst bei hoher Ähnlichkeit niemals verschmolzen werden.

**F05:** Derselbe ERP-Webhook 3-mal mit identischer Event-ID: exakt ein RecoveryEvent, exakt eine FeeAllocation.

**F06:** Werden dieselben Datei- und Regelversionen erneut geprüft, ist das numerische Ergebnis identisch, unabhängig von zwischenzeitlichen LLM-Antworten.

**F07:** Eingangsdaten nur aus Januar bis September bei Jahresbonus: kein „Jahresabschluss erfolgreich geprüft“.

## 10. Technische Quellen

- https://github.com/docling-project/docling
- https://github.com/invoice-x/invoice2data
- https://github.com/frictionlessdata/frictionless-py
- https://github.com/rapidfuzz/RapidFuzz
- https://developers.lexware.io/docs/
- https://docs.frappe.io/cloud/marketplace/publishing-an-app-to-marketplace

**Implementierungsstatus:** null Endpunkte, null produktive Connectoren und null Test-Ergebnisse in LowHangingFruitMe zum 02.11.2026.


## v0.14 private Vertragsprüf-API

- `POST /v1/contract-candidates`: verifizierten Vertrag aus CLEAN-PDF über `contract_upload_id`, Mandant/Gesellschaft, konkrete Agreement-/Rule-/Dokumentrevision im begrenzten Docling-Worker extrahieren. Ergebnis `EXTRACTED`, inklusive SHA-256-fundierter Fundstellen; niemals automatisch freigeben.
- `GET /v1/contract-candidates/{id}`: Fundstellen und Status nur für identischen authentifizierten Reviewer und dessen aktive DB-Mandantenfreigabe.
- `POST /v1/contract-candidates/{id}/review`: geprüfte Regel plus exakte extrahierte Fundstellen und `confirm_clause_review=true` ablegen (`NEEDS_CONFIRMATION`). Keine Geldberechnung.
- `POST /v1/bundles` mit `candidate_id`: nur bei passendem SHA-256-Dokument, Rule-Hash, Revisionsschlüssel, gültigem Reviewer und aktivem Kandidaten. Der eigentliche Übergang `APPROVED` wird atomar mit dem HMAC-Freigabebeleg und dem aktuellen Regelkopf durchgeführt. Replay führt zu Ablehnung; historische Audits bleiben historisch.

Die Testkompatibilität mit ungebundenen Regelbelegen ist **kein** öffentlich aktivierter API-Pfad; der Runtime-Factory-Pfad erzwingt die Kandidatenakte. Echte Parser-/IAM-/Mandanten-Sicherheitsabnahmen bleiben offen.
