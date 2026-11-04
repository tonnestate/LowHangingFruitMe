# LowHangingFruitMe – verschlüsselter Backup-/Restore-Betrieb

Status 04.11.2026: **Code implementiert, synthetische MariaDB-CI getestet; tatsächliche VPS-/DR-Abnahme offen**.

## Schutzumfang und Grenzen

Der Operator-Befehl `lhfm-dr backup` sichert während einer vom Betreiber
bestätigten, vollständig schreibfreien Wartungsphase drei Komponenten:

1. Die dedizierte MariaDB-11.4-Anwendungsdatenbank (inklusive Migrationen
   001–010, Audit, Recovery und Billing-Akten) mit
   `mariadb-dump --single-transaction`.
2. Die ausschließlich private Upload-Ablage `LHFM_UPLOAD_ROOT`.
3. Die private, dem Audit-/Quellensnapshot zugeordnete Ablage
   `LHFM_API_SOURCE_ROOT`.

Alle drei Komponenten werden ohne unverschlüsselte Zwischenarchive direkt
durch `age` verschlüsselt. Ein ebenfalls verschlüsseltes Manifest enthält
pro Tabelle die Zeilenanzahlen, pro Datei Länge/SHA-256 und die Ciphertext-
Prüfsummen aller drei Teile. Der Operator signiert das verschlüsselte
Manifest zusätzlich mit einem **Ed25519-Privatschlüssel**. Die
Wiederherstellung prüft die separat bereitgestellte Signatur-Public-Key-
Datei, bevor überhaupt SQL ausgeführt oder private Dateien angelegt werden.

Jede Zieldatenbank muss manuell vorab erstellt und leer sein; zugelassen
sind ausschließlich Datenbanknamen mit Präfix `lhfm_restore_`.
Der Restore überschreibt weder Bestandsdatenbanken noch private Originale.
Abweichende Tabellenzeilenanzahlen, fehlende Migrationen, falsche
Signaturen, geänderte Ciphertext-Dateien, fehlende/unsichere private
Dateieigentümer, Symlinks und Hardlinks blockieren. Optional werden alle
Dateien in zwei vorab erzeugte, leere 0700-Testverzeichnisse entschlüsselt;
ohne diese werden sie in einem automatisch entfernten temporären Verzeichnis
vollständig auf Original-Hashes geprüft.

## Operator-Voraussetzungen

- Der Python-Laufzeit sind `lowhangingfruitme[registry,auth]`,
  `age`, `mariadb-dump` und `mariadb` lokal verfügbar.
- Ausgehende und laufende Schreibzugriffe des API-, BFF-, Upload-, Audit-,
  Recovery-, Billing- und Hintergrundprozesses sind **nachweisbar
  angehalten**. `LHFM_MAINTENANCE_CONFIRMED=YES` ist lediglich die
  dokumentierte Bestätigung und **kein automatischer Schreibstopp**.
- Upload-/Audit-Quellverzeichnisse sind privat (0700), mit ausschließlich
  privaten Dateien (0600) und konsistenten Eigentümern.
- Die Operator-Konfigurationsdatei ist absolut, Eigentum des ausführenden
  Accounts und 0600; sie enthält einen MariaDB-Client mit
  `host=127.0.0.1`, Port, Benutzer und Passwort. Kein Remote-DB-Ziel.
  Vor dem Testbetrieb die tatsächlich notwendigen Quell-SELECT-/Metadaten-
  und separaten Restore-INSERT-/DDL-Rechte im dedizierten Schema vergeben.
- Die offline verwahrte `age`-Identität bleibt **getrennt** vom
  verschlüsselten Backup und vom öffentlichen GitHub-Repository.
  Der Ed25519-Privatschlüssel liegt nur beim autorisierten Backup-Operator.
  Der unabhängige Verifier benötigt ausschließlich den Public Key.
  Die Eigentümerprüfung lässt den regulären Datei-Eigentümer oder den
  ausdrücklich als root ausgeführten Offline-Operator zu.
- Das Backupziel und die beiden Restore-Dateiverzeichnisse liegen außerhalb
  der Originalablagen und besitzen Rechte 0700.

**Beispiel ohne Zugangsdaten oder echte Pfade:**

```bash
LHFM_MAINTENANCE_CONFIRMED=YES lhfm-dr backup \
  --defaults-file /secure/operator/client.cnf \
  --database lhfm_prod \
  --upload-root /private/lhfm/uploads \
  --source-root /private/lhfm/audit-sources \
  --destination /private/lhfm/backups/backup-20261104 \
  --age-recipient "age1_REPLACE_WITH_REAL_RECIPIENT" \
  --signing-key /secure/operator/manifest-signing.pem
```

Manuell eine **leere** und berechtigte `lhfm_restore_drill`-Datenbank
einrichten, zwei **leere 0700**-Testdateiverzeichnisse bereitstellen und:

```bash
LHFM_RESTORE_REHEARSAL_APPROVED=YES lhfm-dr restore-verify \
  --defaults-file /secure/operator/client.cnf \
  --backup-dir /private/lhfm/backups/backup-20261104 \
  --age-identity /secure/offline/identity.agekey \
  --target-database lhfm_restore_drill \
  --verification-key /secure/operator/manifest-verification.pem \
  --restore-upload-root /private/lhfm/drill-uploads \
  --restore-source-root /private/lhfm/drill-sources
```

Die Signatur-/Schlüsselparameter und Pfade sind verpflichtend;
Platzhalter funktionieren bewusst nicht. Eine neu angelegte, leere
Wiederherstellungsdatenbank ist Voraussetzung; das Programm erstellt,
leert oder löscht selbst **keine** Datenbanken.

## Tatsächlich zu erbringende externe Abnahme

1. Auf dem vorgesehenen VPS die privaten Datenbestände und
   MariaDB-11.4-Datenbank während eines realen Schreibstopps verschlüsselt
   sichern und eine zweite, unabhängige Betreiberperson die
   Ed25519-Signatur-/Empfängeridentität prüfen lassen.
2. Eine vollständig isolierte Restore-Datenbank und zwei leere,
   private Verzeichnisse erzeugen, die Wiederherstellung durchführen,
   `lhfm-schema-check` und die wesentlichen Audit-/Recovery-/
   Billing-Referenzen fachlich nachprüfen.
3. Gemessene Backupzeit, Restorezeit, Datenverlustfenster (RPO),
   Wiederanlaufzeit (RTO), Speicherbedarf und konkrete Fehleralarme
   dokumentieren. Keine vorausgesetzten RPO-/RTO-Werte erfinden.
4. Schlüsselverwahrung, Offsite-Kopien, Alters- und Löschregeln,
   Rotation und den Wiederanlauf des Apache-/BFF-/OIDC-/ClamAV-/
   Docling-Stacks einschließlich Netz-/TLS-Sperren abnehmen.
5. Der Ablauf dient **nicht** als selbstständige automatische
   Rücksicherung auf eine produktive Datenbank und ersetzt keinen
   dokumentierten operativen Cutover-/Rollback-Plan.

## CI-Evidenz

`tests/scripts/ci_dr_rehearsal.sh` erzeugt nur fiktive Upload- und
Auditdateien, eine temporäre `age`-Identität und ein temporäres
Ed25519-Schlüsselpaar. Die echten MariaDB-11.4-Tabellen 001–010
werden in einer CI-Quelle erzeugt, verschlüsselt gesichert und
in eine zweite, isolierte CI-Datenbank zurückgespielt. Ein veränderter
Backupbestand, verfälschte Signaturen und wiederholtes Einspielen
müssen scheitern; entschlüsselte Dateien werden bytegenau verglichen.
Dieser Test beweist **nicht** die Verfügbarkeit von echten Dokumenten,
Dateisystem-Snapshots, Offsite-Disaster-Recovery oder juristischer Freigabe.


## Zusätzliche Schlüssel-/Verzeichnisgrenzen

Der Sicherungslauf lehnt **verschachtelte private Quellverzeichnisse** ab:
Upload- und Audit-Snapshot-Ablagen müssen physisch disjunkt sein.
Sowohl der MariaDB-Client-Credential-Satz als auch der Ed25519-
Signaturschlüssel müssen vollständig **außerhalb** dieser beiden
Quellverzeichnisse und außerhalb des neuen Backup-Ziels liegen.
Während des Restore darf weder die age-Entschlüsselungsidentität noch
der separat gepinnte Ed25519-Public-Key oder der DB-Credential-Satz
innerhalb des eingespielten Snapshot-Verzeichnisses liegen.
Diese Regeln verhindern das versehentliche Einschließen eigener
Trust-Anker und die Verifikation gegen einen vom Backup selbst
mitgelieferten Public Key.
