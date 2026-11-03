# Pilot-Goldstandard – bewusst synthetische Lieferantenbonus-Prüfung

**Kein realer Kundennachweis.** Der nachfolgende Fall ist aus den vorhandenen synthetischen Testfixtures reproduzierbar. Er dient ausschließlich als manueller Sollwert und Regressionstest.

## Unabhängige manuelle Rechenvorlage

| Beleg / Quelle | EUR netto | Bedeutung |
|---|---:|---|
| `Einkauf.csv`: `INV-001` | +210.000,00 | Gebuchte, bonusfähige Einkaufsrechnung |
| `Einkauf.csv`: `RET-001` | −10.000,00 | Gebuchte Lieferantenretoure |
| **Bonusfähige Nettobasis** | **200.000,00** | 210.000,00 − 10.000,00 |
| `rule.json`, `synthetic_contract`: 2 % | +4.000,00 | 200.000,00 × 0,02, Cent-Rundung |
| `Gutschriften.csv`: `CREDIT-001` | −1.500,00 | Bereits gebuchte Jahresbonusgutschrift |
| **Rechnerische Differenz** | **2.500,00** | 4.000,00 − 1.500,00 |
| Gemeldete, unabhängige **manuell attestierte** Realisierung | +1.000,00 | Nur synthetischer gebundener Nachweis |
| **5%-Honorarvorschlag** | **50,00** | 1.000,00 × 0,05; keine Rechnung |
| **Fällig nach Produktabnahmestand** | **0,00** | Keine separate Fakturierungsfreigabe |

Die getrennten Tests `tests/test_promotion.py`, `tests/test_universal_import.py`, `tests/test_recovery.py` und `tests/test_report_exports.py` prüfen diesen Pfad gegen dieselben Sollbeträge. Die Datentypen und Vertragssummen sind synthetisch, auch wenn die Importspalten einem deutschen ERP-Export entsprechen.

## Was genau zu prüfen ist

- Source SHA-256 von `Einkauf.csv` / `Gutschriften.csv` und Originaldokument entsprechen den bei Freigabe fixierten Bytes.
- `REVIEWER-SYN-1` bestätigt eine konkrete FLAT_RATE-Regelrevision, nicht einen von der KI erfundenen Prozentsatz.
- Käuferbelege und Retouren werden nur nach gebuchtem Status und Vertragsperiode berücksichtigt; Gutschriften müssen demselben Vertrag/Zeitraum zugeordnet sein.
- Das getrennte ERP-Kontrollsummen-Protokoll bestätigt nur Übereinstimmung mit seinen angegebenen Werten, nicht die externe Vollständigkeit des ERP.
- Ohne aktive Registry-/Reviewer-Freigabe gibt es keine abschließend evidenzierte Rechnung.
- Ein zweiter Finance-Actor bestätigt die spätere Realisierung. Dies ist eine protokollierte menschliche Prüfung des vorliegenden PDF, **kein unabhängiger Bankabgleich**.
- Ein zurückgenommener Teilbetrag von 500,00 EUR reduziert den Vorschlag von 50,00 EUR auf 25,00 EUR, sofern zuvor nur 1.000,00 EUR bestätigt waren.
- Der Kundendownload muss Rechnungsbetrag, berechnete Differenz, belegte Realisierungen und 5-%-Gebührenvorschlag sichtbar trennen.

## Befund / nicht erfüllte Realitätskriterien

**Kein** echter ERP-Originalexport / Lieferantenvertrag, keine echte OCR-/Docling-Goldannotation, keine Lieferantenantwort, keine Abnahme durch reale Wirtschaftsprüfer oder Kunden, keine rechtliche Verifikationswirkung. Auch der Scan im Test hat keine reale ClamAV-Installation bewiesen. Diese Punkte dürfen nicht als durch die Sollrechnung abgeprüft bezeichnet werden.

Die nächste fachliche Abnahme erfordert einen rechtmäßig anonymisierten, realen Vertrag samt Einkaufs-/Gutschriftenexports und extern freigegebene Kontrollwerte; bis dahin lautet der Status **synthetischer End-to-End-Pilot**.
