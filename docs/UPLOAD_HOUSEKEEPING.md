# Technische Upload-Bereinigung – nur im Wartungsfenster

Status: **v0.18 implementiert; synthetische MariaDB-Tests, keine Kunden-/VPS-Abnahme.**

Das Produkt benötigt eine sichere Behandlung abgebrochener, unvollständiger
Uploads. Die ausschließlich vom Betreiber ausführbare CLI
`lhfm-upload-housekeeping` kann Upload-Intents im Zustand `PENDING` oder
`RECEIVING` nach **Ablauf der Uploadfrist und weiteren 24 Stunden** in
`REJECTED` überführen. Der ursprüngliche Zustand und die Anzahl der
entfernten temporären Dateinamen werden in der eigenständigen
`lhfm_upload_housekeeping_events`-Tabelle revisionsfähig protokolliert.
Die Datenbankmigration `sql/011_upload_housekeeping.sql` fügt einen Index
für die altersgebundene Abfrage und den Ereignisspeicher hinzu.

## Sicherheit und Scope

- **Kein automatischer Timer**, keine öffentliche HTTP-Route und keine
  eigenständige Autorisierung von Personen über Request-Parameter.
- Ohne `--apply` ausschließlich **Dry-run**. Mit `--apply` sind
  `LHFM_UPLOAD_HOUSEKEEPING_APPROVED=YES` und
  `LHFM_UPLOAD_WRITES_STOPPED=YES` erforderlich. Die zweite Variable
  bestätigt eine tatsächlich extern durchgesetzte Schreibpause; sie
  beendet selbst weder Worker noch laufende Requests.
- Der Operator läuft als separater, **nicht-root**-Dienstnutzer, mit
  festem privaten 0700-Staging-Verzeichnis und dedizierten
  loopback-erreichbaren MariaDB-Berechtigungen. Vor dem Start muss die
  geprüfte SQL-Migrationshistorie 001–011 vollständig sein.
- Maximal **100 Upload-Intents pro Aufruf**. Fortsetzung erfolgt nur
  durch erneuten bewussten Aufruf.
- Es werden ausschließlich die auf eine kanonische UUID begrenzten
  Dateinamen `{upload_id}.part` und
  `{upload_id}.inspect{suffix}` geprüft. Der vollständige Upload
  `{upload_id}{suffix}` darf **niemals automatisch entfernt werden**.
  Bereits fertige `CLEAN`- oder `REJECTED`-Datensätze werden
  ebenfalls niemals angefasst, ebenso wenig Verträge, Finanzbelege,
  Kandidaten, Freigaben, Audit- oder Recovery-Akten.
- Sind unerwartete Symlinks/Hardlinks, falscher Eigentümer, öffentliche
  Dateirechte, neue Schreibvorgänge oder eine fertige Datei erkennbar,
  bricht der Operator kontrolliert ab. Eine fachlich unklare
  Situation wird **nicht automatisch bereinigt**.
- Datei-Löschung und SQL-Statuswechsel sind keine verteilte
  ACID-Transaktion. Temporäre Daten werden vor dem Commit unter
  row-level-lock entfernt; scheitert der Commit, bleibt der alte
  DB-Status für eine erneute Wartungsprüfung erhalten. DB-Ereignisse
  werden mit der Zustandsänderung atomar geschrieben.

## Durchführung

1. Mit einer unabhängigen Betriebsprüfung den laufenden API-Dienst und
   die Upload-Worker tatsächlich stoppen. Keine Requests dürfen während
   des Cleanup laufen. Dokumentieren: Zeitpunkt, verantwortliche
   Person, Datenbankversion und erfolgreiches Backup. Nicht bei
   unbeaufsichtigtem Systembetrieb mit aktivem API-Prozess anwenden.
2. Vorher SQL-Migration 011 unter separaten Migrationsfreigaben anwenden;
   dabei gilt das <Link>-freie Verfahren in `docs/DISASTER_RECOVERY.md`
   und `docs/RUNTIME_DEPLOYMENT.md`. Nicht bei App-Start migrieren.
3. Mit der separat und vertraulich bereitgestellten
   `/etc/lowhangingfruitme/api.env`-Konfiguration den Befehl als
   API-Dienstnutzer zunächst **ohne `--apply`** ausführen:

   ```bash
   lhfm-upload-housekeeping --limit 100
   ```

   Dies meldet aggregierte Anzahlen ohne Dateipfade, Personen oder
   Vertragsdaten. Die tatsächliche Ausführung muss denselben
   EnvironmentFile-Inhalt und denselben nichtprivilegierten Benutzer
   verwenden, wie der FastAPI-Dienst.
4. Erst nach festgestelltem Schreibstopp und dokumentierter
   Freigabe kann der Operator in derselben privaten Laufzeitumgebung
   ausführen:

   ```bash
   LHFM_UPLOAD_HOUSEKEEPING_APPROVED=YES \
   LHFM_UPLOAD_WRITES_STOPPED=YES \
   lhfm-upload-housekeeping --apply --limit 100
   ```

   Die Beispiel-Variablen sind **keine** Authentifizierung und ersetzen
   keinen überprüften Wartungsprozess. Niemals dauerhaft in
   `api.env` hinterlegen oder einen ungeprüften Cron/Timer aktivieren.
5. Nach Abschluss die aggregierten Zahlen und die Audit-Events
   kontrollieren. API erst nach erneutem `lhfm-runtime-check` und
   überprüftem `/readyz` wieder hochfahren.

## Verbindliche Grenzen

Dieser Prozess ist **ausschließlich eine technische Hygiene für
unvollständige, überfällige Uploads**. Er löscht keine genehmigten
Geschäftsunterlagen. Er ist keine DSGVO-Löschung, keine
Fristen-/Legal-Hold-Entscheidung, kein Nachweis durchgängiger
Datenträger-Verschlüsselung und keine produktiv erprobte
Systemwartung. Für vollständige Kundendaten-Retention, Sperr-/Lösch-
anforderungen, Backups und rechtliche Nachweispflichten bleiben
G1/G5 bis zur externen Prüfung offen.
