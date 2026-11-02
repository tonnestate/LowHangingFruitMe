# Security policy

LowHangingFruitMe is **pre-production** financial-data analysis software. Do not upload customer contracts, live invoices, API credentials or customer financial statements to this public repository.

## Boundaries

- Existing intake commands accept local files only. They are **not** a secure multi-tenant upload service.
- PDF processing requires isolated worker processes, malware scanning, egress restrictions, timeout and memory limits before receiving actual customer data. The current Docling adapter does **not** provide OS process isolation.
- Frictionless validates structural CSV input; it cannot prove the commercial completeness of submitted data.
- No raw customer data may be transmitted to third-party AI services without contractual, security and customer authorization.
- No automatic legal-claim determination, supplier communication, recovery action or invoicing exists.

## Vulnerability disclosure

Report vulnerabilities privately via GitHub private vulnerability reporting when available, or request a secure contact from the repository owner. Never post exploit instructions with secrets or customer records as a public issue.

## Production release requirements

Tenant and role isolation, secure upload pipeline, independent completeness controls, at-rest encryption, retention and deletion, dependency/SBOM review, execution sandbox, end-to-end and security testing, backup/restore proof, and contractual/legal approval.
