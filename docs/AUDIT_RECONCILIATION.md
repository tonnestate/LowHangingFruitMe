# Audit-Unterbrechungen: sichere manuelle Reconciliation (SQL-012)

Die Audit-API führt den deterministischen Finanzkern synchron aus und
reserviert vor dem Start eine Idempotency-Key-gebundene MariaDB-Zeile.
Bei einem OS-/Worker-Abbruch vor `finish_run` kann `PROCESSING` dauerhaft
bestehen bleiben. Weder ein HTTP-Timeout noch ein hohes Alter beweist,
dass der Worker tatsächlich beendet ist. Deshalb gibt es **kein**
automatisches Rekalkulieren, keine automatische Statuskorrektur und kein
Recycling eines verwendeten Idempotency-Key.

Die gesonderte Operator-CLI `lhfm-audit-reconcile` prüft exakt **einen**
Audit in seinem Mandanten-/Gesellschafts-Scope; Vorschau ist Standard.
Ein Audit darf nur nach mindestens 60 Minuten, nach **wirklich
vollständigem** Stopp sämtlicher Audit-Worker auf allen Hosts und nach
extern dokumentierter Freigabe in den bestehenden Status `FAILED`
überführt werden. Der Operator muss zuvor prüfen, dass keine Arbeit
mehr läuft und keine finanziellen Ergebnisse extern übernommen wurden.

Beispiel einer read-only Vorschau:

```bash
lhfm-audit-reconcile --audit-id UUID --tenant-id TENANT --legal-entity-id ENTITY \
  --operator-id OPERATOR --incident-ref INCIDENT
```

Nach bestätigtem Wartungsfenster, überprüftem Worker-Stopp und
erfasstem Incident, ausschließlich als unprivilegierter Prozess:

```bash
LHFM_AUDIT_RECONCILIATION_APPROVED=YES LHFM_AUDIT_WORKERS_STOPPED=YES \
lhfm-audit-reconcile --apply --audit-id UUID --tenant-id TENANT \
  --legal-entity-id ENTITY --operator-id OPERATOR --incident-ref INCIDENT
```

Die Datenbank ändert ausschließlich `PROCESSING -> FAILED` und
protokolliert den Vorgang im unveränderlich angelegten Event
`lhfm_audit_reconciliation_events`. Row-Level-Lock,
Source-State-Prüfungen, zeitlicher Mindestabstand und eine eindeutige
Event-Constraint verhindern versehentliche Wiederholung.
`report_json`, Originalbelege, Dokumentenstände, Recovery/Billing
und der ursprüngliche Idempotency-Key bleiben unverändert.
Der Kunde kann nach neuer fachlicher Quellen-/Regelprüfung mit **neuem**
Idempotency-Key einen neuen Audit beantragen. Ein bestehender Audit
wird niemals als derselbe abgeschlossene Audit ausgegeben.

**Wichtige Grenze:** Die CLI prüft nicht automatisch, ob tatsächlich
jeder Worker auf sämtlichen Servern beendet wurde. Die beiden
Umgebungsfreigaben ersetzen keine reale Betriebskontrolle. Das
Verfahren ist kontrollierte Störungsbehandlung, keine persistente
asynchrone Jobqueue. Es wurden keine Live-Kundendaten bearbeitet.

Die bestehende private API zeigt bei einer seit mindestens 60 Minuten offenen `PROCESSING`-Reservierung das Feld `operator_reconciliation_required=true` sowohl in der GET-Antwort als auch bei einem idempotenten POST-Replay. Das bleibt ein **Hinweis**, nicht die Erlaubnis, ohne extern kontrollierten Worker-Stopp einen Auftrag zu verändern. Eine neue Browser-Sitzung zeigt diesen Zustand nach erfolgreicher rollen-/mandantenautorisierter Audit-Wiederaufnahme.


## SQL-013 – Ausschluss doppelter Berechnungen

Eine neue MariaDB-Unique-Constraint auf (Mandant, Gesellschaft, Reviewer, signiertes Bundle) verhindert auch bei direkten API-Aufrufen, parallelen Requests oder fremden Idempotency-Keys eine zweite Ausführung desselben geprüften Datenpakets. Die API antwortet in diesem Fall mit `409 IDEMPOTENCY_CONFLICT`; ursprüngliche Belege und Ergebnisse bleiben unverändert. Der Migration Runner prüft vor dem SQL-013-DDL auf bereits vorhandene mehrfache Audits und hält **ohne IN_PROGRESS-Markierung oder Löschung** an. Bestandsfälle müssen separat geprüft werden; keine automatische Deduplikation von Finanzdaten. Für einen echten neuen Audit ist ein neu geprüftes, signiertes Bundle erforderlich.
