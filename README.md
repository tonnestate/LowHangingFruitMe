# LowHangingFruitMe

**FruitStack Revenue-Recovery-Produkt: nicht realisierte Lieferantenboni und Konditionsdifferenzen aufspüren, nachvollziehbar berechnen und tatsächlich realisierte Rückvergütungen abrechnen.**

Status (02.11.2026): **Konzept / keine Produktimplementierung / keine Live-Kundendaten / keine validierten Rückgewinnungsraten.** Dieses öffentliche Repository enthält keine vertraulichen Kunden-, Vertrags- oder FruitStack-Daten.

## Verbindliches Zielbild

- Eigenständiges B2B-Kundenportal mit geschütztem Upload.
- Versionierte REST-API für Upload, Prüfaufträge, Evidenz, Status und später ERP-Connectoren.
- KI liest und strukturiert Vertragsklauseln; deterministische Engine berechnet Ansprüche.
- Beleggestützte Differenzfälle mit Vollständigkeits- und Unsicherheitskennzeichnung.
- Kunde betreibt die kaufmännische Lieferantenklärung selbst. Keine automatische Forderungseinziehung.
- Erfolgsvergütung als zu prüfendes Modell: 10 % ausschließlich auf nachgewiesene, zurechenbare, tatsächlich realisierte zusätzliche Nettovergütung.
- Keine ERP-Neuentwicklung, kein Duplikat des FruitStack-Orchestrators, kein direkter Zugriff auf andere Produktdatenbanken.

## Konzeptdokumente

1. [Produkt und Architektur](docs/CONCEPT.md)
2. [GitHub-Donoren und Übernahmebedingungen](docs/DONORS.md)
3. [Datenmodell, API und Prüfregeln](docs/API_AND_DATA.md)
4. [Vertragsmodell, Erlöserfassung und Datenschutz](docs/LEGAL_AND_REVENUE.md)
5. [Implementierung, Abnahme und Markteintritt](docs/DELIVERY_PLAN.md)

## Evidenzregel

VERIFIED bedeutet: anhand verlinkter Quelle / konkretem Repo-Dateiinhalt nachvollzogen. PLANNED bedeutet: für LowHangingFruitMe spezifiziert, aber nicht implementiert. UNVERIFIED bedeutet: noch durch Tests, Verträge, technische Freigaben oder reale Kundendaten zu klären.

Es wurde kein Fremdcode kopiert oder ausgeführt. Donoren sind Auswahlkandidaten, keine unüberprüft installierten Abhängigkeiten.
