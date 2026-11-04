# Docling-PDF-Sandbox: technische Abnahme

Status: **Fail-Closed-Schnittstelle implementiert, kein nachgewiesener VPS-Betrieb**.

Die Python-API darf den Vertragsparser nicht im Webprozess ausführen. Der
neue Betriebsparameter `LHFM_DOCLING_SANDBOX_LAUNCHER` bezeichnet
eine absolut adressierte, ausführbare Datei unter einem ausschließlich
von root kontrollierten Verzeichnispfad. Symlinks und für Gruppe/Andere
beschreibbare Eltern oder Startdateien sind unzulässig.

Der Launcher bekommt fünf Argumente: Python-Interpreter, `-I`, `-m`,
`lowhangingfruitme.documents_worker`, PDF-Pfad oder `--preflight`.
Er muss einen eigenen PID-/Mount-/Netzwerk-Namespace, keine
Netzwerkverbindung, begrenzten Dateizugriff, offline vorhandene
Modelldateien und einen unprivilegierten Betrieb sicherstellen.

Der Worker selbst prüft zwingend, dass sein Netzwerk-Namespace vom
aufrufenden API-Prozess abweicht und lediglich ein Loopback-Interface
sichtbar ist. Andernfalls verweigert er die Ausführung. `GET /readyz`
startet tatsächlich den Prüfprozess und verweigert bei ungültigem
Launcher oder fehlender Isolation die Bereitschaft. Der lokale
Operatorcheck lautet `lhfm-docling-check`; der Rückgabecode 0
bescheinigt **ausschließlich** die getestete Netzisolation.

Die Extraktion liest stdout inkrementell mit höchstens 1 MiB,
120 Sekunden Laufzeit und beendet bei Zeit-/Ausgabelimit die
gesamte Prozessgruppe. CPU-, RAM-, Dateigrößen- und
Dateideskriptorgrenzen setzt der Worker selbst; das unsichere
Python-`preexec_fn` im mehrthreadigen Webserver wird nicht mehr
verwendet.

## Hostinstallation

`deploy/docling-bwrap-launcher.sh.example` ist eine **an Host und
Python-Installation anzupassende Beispielvorlage** für Bubblewrap,
keine einsatzfertige oder auf dem VPS geprüfte Konfiguration. Das
Beispiel setzt ein Wheel-installiertes Venv und eine vollständig offline
bereitgestellte Docling-Modellablage unter `/srv/lowhangingfruitme/`
voraus. Vor der Übernahme die Pfade, Berechtigungen, Linux-Namespaces
und die Bubblewrap-Version sowie Paketinhalte prüfen.

Die angepasste Datei als `root:root` mit Modus `0755` in einem
root-kontrollierten Pfad installieren. Den Server mit separater
unprivilegierter Service-Identität starten. Danach
`LHFM_DOCLING_SANDBOX_LAUNCHER=... lhfm-docling-check` und
`GET /readyz` am echten Host ausführen.

Zusätzliche zwingende Abnahme: tatsächliche textbasierte und
gescannte Dokumente einschließlich OCR/Tabellen, abweichende
Docling-Versionen, Parserfehler, manipulierte PDF, abgesicherter
Dateisystemzugriff, fehlende Modelle, Ressourcenlimits,
Konkurrenzlast und kontrolliert blockierter Egress. Für jede
finanzrelevante Klausel bleibt die unabhängige fachliche Prüfung
des Originaldokuments verpflichtend.

**Grenze:** Netzwerk-Namespace-Unterschied plus ausschließlich
Loopback-Interface ist eine konkrete Laufzeitkontrolle, keine
vollständige OS-Sandbox-, Malware- oder Lieferkettenattestierung.
Ohne realen Hosttest und externe Freigaben bleibt der öffentliche
Vertragsupload gesperrt.
