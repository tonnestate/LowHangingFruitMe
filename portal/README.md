# Deployment – own Apache VPS, isolated Next.js service

**Current state: deployment configuration only. No changes to production Apache, WordPress, DNS, TLS, systemd or server contents were performed by this repository update.**

## Isolation principle

- Next.js marketing application lives in \`portal/\`; existing Python financial engine and MariaDB remain separate.
- One unprivileged systemd process on **127.0.0.1:3107**; the port is a suggested isolated local binding and **must be checked for conflicts before deployment**.
- Add a *new* Apache VirtualHost for an **owner-selected domain**. Do not edit existing TonnEstate/WordPress vhosts or reuse their DocumentRoot.
- Expose only Apache HTTPS; do not publicly expose port 3107.
- An OIDC-protected operator workspace and authenticated API proxy are implemented **in source** but not enabled for real customer traffic on the VPS. The public marketing pages still do not accept customer finance documents; there is no real invoicing service.
- Until real legal operator details, privacy information, domain TLS and a security review and full operator-provided legal texts are completed: \`PUBLIC_LAUNCH_APPROVED=false\`. This generates \`noindex\` and a full robots disallow.
- Missing contact email means the request page **shows a transparent disabled staging message**, not a success screen or an unhandled form.

## Versions, build and locally reproducible tests

Requires Node.js 20.9+, preferably supported LTS (the CI uses Node.js 22). From the repository root:

\`\`\`bash
cd portal
npm install
npm test
npm run build
npm run typecheck
npm run pack:standalone
HOSTNAME=127.0.0.1 PORT=3107 node .next/standalone/server.js
\`\`\`

The \`prebuild\` phase reads \`../docs/Neon-Low-Hanging-FruitMe-Banner.png\`, generates pixel-evidenced CSS brand colors, a measured provenance JSON and an **identical** banner copy. The source PNG remains unchanged. Generated assets are not committed. Builds fail if the source PNG is unavailable, invalid or lacks a readable dark/light contrast pair.

The file \`portal/public/brand-measurement.json\` records sampled original pixel coordinates, HEX values, SHA256 and contrast measurement. It is not a license to invent an alternate logo/palette.

## Apache and systemd templates

- \`deploy/apache-vhost.conf.example\`: replace \`SITE_DOMAIN.invalid\` and TLS certificate paths with actual assigned values. Review existing listeners, proxy modules, HTTPS certificates and Apache vhosts **before** enabling the site.
- \`deploy/lowhangingfruitme-portal.service.example\`: configure a dedicated service account and own directory. No root service.
- Place the built standalone application under an isolated path, such as \`/srv/lowhangingfruitme/portal\` with its own permissions, not inside any WordPress directory.
- systemd environment should not expose financial database credentials or signing keys: this is a marketing-only service.

### Release check before even staged server activation

1. Verify domain ownership, DNS and TLS, vhost collision and localhost port usage.
2. Check host RAM/CPU/disk and reserve a bounded Node process. Do not compromise the existing Apache/WordPress services.
3. Run the real GitHub frontend test workflow and verify its screenshot evidence at 1440, 768, and 390 pixels.
4. Run \`apachectl configtest\` before enabling the new VirtualHost.
5. Verify \`curl -I\` response and expected noindex/robots on the chosen staging hostname.
6. Validate accessibility, CSP/content security (including future external integrations), security headers, backup and logging.
7. Obtain and publish correct \`Impressum\`, full \`Datenschutzerklärung\`, incident contact, and verify 3% commercial terms independently before public indexation.

\`PUBLIC_LAUNCH_APPROVED=true\` is deliberately blocked unless an HTTPS site URL, operator/contact details, legal review and security approval flags are supplied. **This flag check is not an independent legal opinion.** The staging privacy text is explicitly incomplete; public builds are blocked without at least 500 characters of operator-provided reviewed privacy text and additional imprint disclosure. Passing environment flags is not legal advice.

## Follow-on application boundary

Any future customer portal or upload API must use its own authenticated backend, tenant isolation and private encrypted document storage. Do not couple lead collection or financial workflows to this static marketing app until the full identity, consent, retention and security design is accepted.

## Current v0.12.0 source-only operator flow

`/arbeitsplatz` is guarded by server-side OIDC session checks; the allowlisted `/api/finance/*` Next.js BFF forwards only approved JWT-scoped routes to `LHFM_API_INTERNAL_URL` at a loopback origin. It supports upload intent/content, inspect source, reviewed contract bundle, audit run, recovery evidence and independent finance review. Report downloads `report.pdf`, `report.xlsx`, `report.json` are forwarded as binary-safe, no-store replies after the Python API checks reviewer/tenant/ledger permissions.

This is a tested development flow, **not** proof of the customer's chosen identity provider, deployed server settings, TLS hardening, ClamAV daemon, retention, customer consent or legally billable fee. The existing neon PNG remains the only permitted visual brand source. See `../docs/FOUR_WEEK_ACCEPTANCE.md`.


## Dokumentengebundene v0.14-Regelfreigabe

Das Arbeitsportal verlangt vor einer signierten Audit-Registrierung jetzt die
Extraktion und ausdrückliche Auswahl einer verifizierbaren Fundstelle aus einer
gescannten Vertrags-PDF. Der gesonderte API-Kandidat durchläuft EXTRACTED,
NEEDS_CONFIRMATION und APPROVED; die endgültige Freigabe erfolgt nur in der
MariaDB-Transaktion der signierten Regelrevision. DOCX-Verträge sind im ersten
schlanken Pilotablauf nicht zugelassen. Ein grüner Browser-Test belegt noch
keine produktive Docling-Modellinstallation, Betriebssystem-Sandbox oder
unabhängige juristische Vertragsauslegung.
