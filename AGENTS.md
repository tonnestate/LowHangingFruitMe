# LowHangingFruitMe – implementation guardrails

## Authoritative sources
Read actual GitHub main HEAD and these files before editing: docs/CONCEPT.md, docs/DONORS.md, docs/API_AND_DATA.md, docs/LEGAL_AND_REVENUE.md, docs/DELIVERY_PLAN.md and docs/IMPLEMENTATION_STATUS.md. A statement in a document is not proof of implementation.

## Engineering contract

1. Change only the requested workstream. Integrate into the actual program path rather than building an unrelated second implementation. Keep main installable and tested.
2. Money = Decimal, explicit cent rounding and exact contract semantics; never silently infer ambiguous tiers, supplier identity, FX, credit-note attribution or data completeness.
3. Every computed line must link to source ID, original file hash/page or row, rule version and calculation version. Source content is untrusted.
4. A model may propose rules but cannot approve or authoritatively calculate a contractual monetary entitlement.
5. A calculated difference is **not** a legally established claim, realised recovery or automatically billable success fee.
6. Do not add whole ERP backends, new DBs, cloud AI services or duplicated FruitStack orchestration without explicit need and verification.
7. No customer data, passwords, private FruitStack code or live financial records in this public repo.
8. Every donor must have source, licence, dependency provenance, reproducible test and benchmark before being called integrated or production ready.
9. External actions require authority and idempotency. No automated supplier communication, Inkasso or invoice creation based merely on an LLM proposal.
10. Document actual commands, result evidence and gaps; no fabricated CI/production claims.

## Verification commands

    python -m pip install -e ".[import]"
    python -m unittest discover -s tests -v
    python -m compileall -q src tests
    python -m lowhangingfruitme.cli tests/fixtures/flat_rebate.json
    lhfm audit-csv --rule tests/fixtures/rule.json --transactions tests/fixtures/transactions.csv --settlements tests/fixtures/settlements.csv --source-system sample-erp --confirm-transactions-complete --confirm-settlements-complete --confirm-agreements-complete

Docling integration requires separate optional installation and real PDF acceptance on the actual deployment host.
