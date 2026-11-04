# LowHangingFruitMe – verbindliche Go-Live-Abnahme

Status: **NOT READY FOR PUBLIC/PAID CUSTOMERS**. Die technischen GitHub-Tests ersetzen keine reale Betriebsfreigabe. Ein erfolgreicher Unit-Test oder eine gefälschte Umgebungsvariable darf kein Gate schließen.

## G0 – Identität und Kundenzugriff: OPEN

Einen realen OIDC-Provider registrieren, ausgehende Access Tokens mit `at+jwt` und tatsächlicher API-Audience verifizieren, Session-Renewal/Refresh/Logout, MFA-Anforderungen, Entzug und echte Mandantentrennung einschließlich Cross-Tenant-/Replay-Tests nachweisen. Bereitgestellte JWKS müssen atomar und revisionssicher aktualisiert werden.

## G1 – Daten und Dokumente: OPEN

Eigenen gesicherten Server mit HTTPS, Apache-/BFF-Proxies, verschlüsselter Dateihaltung und MariaDB-Backups betreiben. Reale ClamAV-Installation und aktuelle Signaturen, angegriffene ZIP/XML/PDF-Dateien, 16-MiB-Grenze, Retention/Lösch-Workflow und Restore testen. Docling nur unter eigener eingeschränkter OS-Identität mit überwachten RAM/CPU/Timeout-Limits, **nachweislich gesperrtem Netz-Egress** und lokal bereitgestellten Modelldateien starten; tatsächliche Bild-PDFs und mehrseitige Tabellen mit kontrolliertem Goldstandard prüfen. Der Python-Subprozess allein ist keine Sandbox.

## G2 – Vertrag/Regel: CODE IN REVIEW, EXTERNAL OPEN

PDF-Kandidatenstufen EXTRACTED → NEEDS_CONFIRMATION → APPROVED und SUPERSEDED/REVOKED einschließlich Mapping/Revocation/Concurrency im gesamten API-/Portalpfad synthetisch abnehmen. Eine externe Fachperson muss die ursprüngliche Klausel einschließlich Nachträge, Satz und Zeitraum mit dem generierten Regelbefund kontrollieren. KI-Ergebnisse sind nur Vorschläge und keine juristische Interpretation.

## G3 – unabhängige ERP-Quellenlage: OPEN

Ein legal bereitgestellter echter, lesender ERP-Datensatz mit 12 Monaten und kontrollierten unabhängigen Kontrollsummen; Pilotziel: mindestens 200.000 EUR Nettobasis, mindestens 95 % wertgewichtete Quellenabdeckung und höchstens 10 % ungeklärte Posten. Testdaten und selbsterzeugte Kontrollsummen sind keine externe Vollständigkeitsprüfung. Lexware Office P1 bei tatsächlichem Testkonto durchführen.

## G4 – Recovery, Honorar und Recht: OPEN

Echte Buchungs-/Bank-/Verrechnungsbelege unabhängig prüfen, Teilrealisierung, Rückgabe, Fallrevisionen, Entgeltsatz und verbindliche Kundeneinwilligung vor jeder kaufmännischen Fälligstellung prüfen. `fee_due_net` bleibt Null, bis ein autorisierter Rechnungsfreigabeprozess und externe RDG-/Vertrags-/Datenschutzprüfung dokumentiert sind. Keine automatische Lieferantenansprache, Rechtsberatung oder Inkassotätigkeit.

## G5 – Release und Observability: OPEN

Python-/Browser-/Sicherheits-/Lasttests, reproduzierbare dependency locks/SBOM, Schema-Migration 001..009 mit Prüfsummen und tatsächlich wiederhergestelltem Backup, Release-Rollback, Monitoring/Alerting, Fehlerbehandlung, Secrets- und Schlüsselrotation, DSGVO-Datenlöschung und Incident-Runbook auf dem vorgesehenen VPS abnehmen. Vorher `PUBLIC_LAUNCH_APPROVED=false` belassen.

**Vollständige Produktivfreigabe:** Erst wenn für G0–G5 konkrete externe Belege, zuständige Entscheider und Abnahmedaten vorliegen. Keine Behauptung einer erfolgten Freigabe aus CI allein.
