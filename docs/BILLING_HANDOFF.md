# Zweipersonen-Honorarübergabe (v0.15)

**Status:** Implementierter kaufmännischer Übergabeprozess mit synthetischen
MariaDB-/API-Tests. Keine automatischen Rechnungen, kein Inkasso, keine
tatsächliche juristische Freigabe und keine unabhängig geprüften Bankbelege.

## Einbindung

Die bestehende Audit-/Recovery-Engine bleibt die maßgebliche Quelle.
Vertragsbezogene Differenzen werden nicht direkt abrechenbar.
`lhfm_commercial_terms` enthält ausschließlich vom Betreiber
**außerhalb der öffentlichen API** nach Prüfung freigegebene
Kundenannahme- und externe Rechtsprüfungsnachweise für
Mandant, Gesellschaft und Vertragskennung. Die Rate (300/500 bps) muss
exakt der unveränderlichen Rate der Recovery Case entsprechen.
`lhfm_billing_grants` erlaubt gesonderte, aktiv erteilte Billing-Rollen.
Ein positiver Datenbankeintrag allein ist kein tatsächlicher
Wirksamkeits- oder Zahlungsnachweis; ihn muss eine unabhängige
Betriebsfreigabe begleiten.

## Workflow

1. Finanzprüfer bestätigt einen wirtschaftlichen Recovery-Eingang gegen
   den gescannten Originalbeleg; er darf nicht dessen Meldender sein.
   Das ist weiterhin eine dokumentierte Rollenbestätigung, **keine
   automatische Bankbestätigung**.
2. Ein Billing-Bearbeiter mit `lhfm:billing:prepare` erstellt mit
   `POST /v1/audits/{audit_id}/billing-packets` die nach Mandant,
   Gesellschaft, Vertrag und vollständigem Ereignisbestand fixierte
   `PREPARED`-Akte.
3. Ein zweiter, separat berechtigter Billing-Bearbeiter bestätigt
   den *aktuellen* Originalstand mit
   `POST /v1/billing-packets/{packet_id}/release` und
   `confirm_commercial_terms_review=true`.
   Nur eine weiterhin gültige, out-of-band erfasste kommerzielle
   Vereinbarung mit passender Rate wird akzeptiert. Ein geänderter
   Recovery-Stand, ein unbestätigter Beleg, ein gesperrter Vertrag,
   ein anderer Mandant oder ein älterer offener Release führt zum
   Abbruch. `RELEASED` bezeichnet **nur** die interne
   Übergabe an die externe Rechnungserstellung.
4. Mit `GET /v1/billing-packets/{packet_id}` erhält ein
   aktiver Billing-Bearbeiter die eingefrorene, belegbezogene
   Rechnungsgrundlage. `invoice_created=false` und
   `fee_due_net=0.00` bleiben bis zum realen Rechnungsnachweis
   gesetzt. Dieser Endpunkt ist keine Steuer- oder E-Rechnungsdatei.
5. Bei späterer Stornierung, neuer Realisierung, Rückbuchung
   oder einem Streitfall meldet die API eine veraltete Akte.
   Für ein zuvor freigegebenes Paket muss ein ermächtigter
   anderer Billing-Bearbeiter die *manuelle externe
   Rechnungs-/Gutschriftkorrektur* referenzieren und die Akte über
   `POST /v1/billing-packets/{packet_id}/void`
   protokolliert widerrufen. Ohne diesen Nachweis gibt es keine
   erneute Freigabe. Neue Netto-Basis und entsprechendes
   Honorar werden erst in einer neuen Akte berechnet.

Die Protokollierung ist append-only (`lhfm_billing_packet_events`).
Transaktionen sperren den Recovery Case, damit eine zeitgleiche
Freigabe/Realisation/Reversal nicht an einer Stale-Prüfung vorbeikommt.
Eine frühere RELEASED-Akte bleibt historisch lesbar, auch wenn eine
spätere Korrektur ihren Zustand verändert. Ein historisch identischer
VOIDED-Fingerprint wird nie still erneut freigegeben.

## Zugriffsrechte

- `lhfm:billing:prepare`, `lhfm:billing:read`,
  `lhfm:billing:release`, `lhfm:billing:void`
  werden per signiertem API-JWT geprüft.
- Zu jeder Operation wird die aktive Billing-Rollenfreigabe
  in der zugehörigen, mandantenspezifischen MariaDB-Struktur
  zusätzlich unter Transaktionssperre geprüft.
- Bearbeiter dürfen ihre eigenen PREPARED-Akten weder RELEASEN
  noch VOIDEN. Die Berechtigung zur Recovery-Bestätigung
  ist weiterhin separat.
- Keine API erlaubt es, den vermeintlichen Rechtsfreigabehash
  oder Gebührenvertrag mit einem Client-Bool zu erzeugen.

## Vor echter Rechnungsstellung zwingend

Ein fachlich unterzeichneter Kundenauftrag mit Erfolgshonorar,
externe RDG-/Datenschutz-/Steuerprüfung, tatsächliche
Zahlungs-/Verrechnungsnachweise, kontrollierte Datenquelle und
ein echter Rechnungsaussteller sind erforderlich. XRechnung,
Umsatzsteuer, Rechnungsnummern, Zahlungseingangsabgleich und
Korrektur-/Gutschriftsworkflow außerhalb des technischen
Handoffs müssen separat abgenommen werden. Ein Release des
Handoffs darf nicht als fällige Rechnung oder Zahlung behauptet werden.

SQL-Migration: `sql/010_billing_handoff.sql`, ausschließlich
nach freigegebener Sicherung durch das prüfsummengebundene
Wartungstool, niemals vom Webprozess ausgeführt.
