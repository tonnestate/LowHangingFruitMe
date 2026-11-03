# LowHangingFruitMe – prüfbare Abnahme des Vier-Wochen-Plans

**Stand:** 03.11.2026 | **Code:** v0.12 Entwicklungsstand | **keine Produktiv- oder Kundenabnahme**

Status: **PASS** = durch CI mit synthetischen Daten nachgewiesen, **TEILWEISE** = technische Teilfunktion, **OFFEN** = nicht umgesetzt/nicht belegbar. Aus einem abgeschlossenen Wochenplan folgt keine rechtsgeschäftliche oder datenschutzrechtliche Freigabe.

## Woche 1 – Daten bis Differenz und Recovery-Ledger

| Kriterium | Bewertung / Nachweis |
|---|---|
| CSV/XLSX-Mapping → Freigabeprüfung → Audit → Report in einem lokalen Aufruf | **PASS**: `lhfm audit-sources` verwendet bereits zuvor signierte, in MariaDB registrierte Regel-Freigabe; erzeugt keine neue Berechtigung. Negativtest für unsigned receipt. |
| Report trennt `calculated_variance_net`, `billable_recovery_net`, `fee_due_net` | **PASS**: explizite Felder und 0.00 solange kein autorisierter kaufmännischer Abrechnungsprozess existiert. |
| Persistente Fälle und Realisierung | **PASS**: `sql/004_recovery_ledger.sql`, zwei-Akteur-Verifikation, idempotente Gutschrift/Storno-Protokolle. |
| Fallstatus NONE/CLAIMED/REALIZED_PARTIAL/REALIZED_FULL/DISPUTED/CLOSED | **PASS**: abgeleitete bzw. manuell per Finanzprüfer signalisierte Zustände in `sql/005_recovery_case_status.sql`. |
| Keine Geldbehauptung bei Readiness-/Approval-Fehler | **PASS**: bestehende Sicherheitsgates und Negativtests. |

## Woche 2 – sichere Mapping-/Regelfreigabe

| Kriterium | Bewertung / Nachweis |
|---|---|
| Authentifizierter Mapping-Reviewer und dokumentiertes Mapping | **PASS**: JWT-Subjekt wird geprüft, Quell- und Mapping-Hash werden in privaten, kopierten Quellenbündeln dokumentiert; signierter Vertrag mit Dokument-/Regel-Hash in MariaDB. |
| **Eigenständige Mapping-HMAC-Bestätigung mit Registry-Eintrag** | **OFFEN**: es gibt noch keinen separat signierten, versionierten Mapping-Freigaberecord. Nicht als erledigt kennzeichnen. |
| Docling + Vertragsregel + Original als ein Freigabeobjekt | **TEILWEISE**: Vertragsoriginal und vom Prüfer manuell eingetragene Regel werden gemeinsam freigegeben; Docling-Extraktion ist ein getrennter Prototyp. |
| Vollständige Regel-Lifecycle-State-Machine mit SUPERSEDED | **OFFEN**: unterschriebene HMAC-Approval und Revoke vorhanden, vorgeschlagene Statusübergänge nicht vollständig modelliert. |
| Negative Datenszenarien | **PASS**: fehlende Spalten, widersprüchliche Kontrollsummen, unklare/nicht implementierte Staffel-Semantik werden abgewiesen oder als Review/Not Calculable markiert. |

## Woche 3 – Goldstandard und Berichte

| Kriterium | Bewertung / Nachweis |
|---|---|
| Realitätsnah nachgebaute Import- und Vertragsbelege | **PASS – synthetisch**: DE-ERP-CSV/Excel mit Einkauf, Retoure, Bonusgutschrift, Vertragsregel und Kontrollen. |
| Manuelle unabhängig formulierte Sollrechnung | **PASS – synthetisch**: `PILOT_GOLDSTANDARD.md`; EUR 210.000 - 10.000 = 200.000, 2% = 4.000, vorliegende Gutschrift 1.500, rechnerische Differenz 2.500. |
| Evidence IDs/Hash/Regelrevision/Lineage | **PASS mit Einschränkung**: Quellen-Hashes und Transaktionsreferenzen im Kundenbericht, vollständige Zeilen-Lineage bleibt im privaten Snapshot, nicht im PDF. |
| PDF/XLSX/JSON Kundenexport | **PASS**: real erzeugte PDF-/XLSX-Bytes sowie parsebares JSON mit HTTP-/Sicherheitstests. |
| Echte, rechtmäßig bereitgestellte externe Pilotdaten und manuelle fachliche Abnahme | **OFFEN**: keine echten Unternehmensdaten oder Originalvertrags-Benchmarks verfügbar. |

## Woche 4 – Portal, Upload, Status, Sicherheit

| Kriterium | Bewertung / Nachweis |
|---|---|
| Authentifizierter Browser-Operator-Pfad | **PASS – synthetisch/staging**: OIDC Next.js-BFF, FastAPI-Rollenscopes, Mail-/ERP-freie lokale Testtokens. |
| Upload mit MIME/Grenzen/Scanner-Prüfung | **PASS – Testadapter**: Scanner-Mock in CI und fail-closed ClamAV-Socket-Anbindung; **kein** produktiver laufender Scanner auf VPS. |
| Bericht-Download nach Mandant-/Rollenzugriff | **PASS – CI**: BFF-Allowlist, zusätzlicher Ledger-Lesescope, PDF/XLSX/JSON. |
| Realisierungsmeldung und 3%-Gebührenvorschlag | **PASS – Vorschlag**: unabhängige manuelle Finanzverifikation. Für **rechtsverbindlichen `billable_recovery_net` / `fee_due_net`** fehlt die gesonderte vertragliche und buchhalterische Gebührenfreigabe. |
| Kundenbetrieb, echte Isolation/Retention, Rechtsprüfung, Auth-Konfiguration | **OFFEN**: keine reale Kundenabnahme, kein externes IdP-Provisioning, kein produktiver VPS-Deploy, keine SOC-2-Type-II-Prüfung, keine vollständig geprüften Verträge/AVV/TOMs. |

## Verbindliche Definition des nächsten Abnahmegates

Ein kommerziell demonstrierbarer Pilot erfordert: (1) vollständiges und freigegebenes Vertrags-/Mandats-Setup, (2) rechtmäßig beschaffte, plausibilisierte ERP-Daten, (3) manuellen Goldstandard mit Belegprüfung, (4) durchlaufene Auth-/Upload-/Gates, (5) tatsächliche belegte Auszahlung/Verrechnung **oder deutlich als Simulation markierte Realisierung**, (6) saubere 3%-Honorarfreigabe ohne automatische Rechnungsstellung, (7) produktiv validierten Sicherheitsbetrieb. Kein Code-Commit kann externe reale Belege oder Zertifikate ersetzen.
