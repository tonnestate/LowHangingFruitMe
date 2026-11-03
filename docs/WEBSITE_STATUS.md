# Website implementation and acceptance – LowHangingFruitMe portal 0.1.0

**Date:** 2026-11-03  
**Python backend:** v0.7.0, unchanged  
**Marketing frontend:** new Next.js 16 / React 19 portal, standalone app in the existing repository  
**Deployment status:** **not installed on the production VPS**. No DNS, Apache, TLS, WordPress or systemd changes have been made.

## Purpose and data separation

The frontend is a dedicated German acquisition and educational website on the operator's existing webserver, not a WordPress page. It is **not** yet a customer portal, financial data upload, authenticated API or account-management app. All financial computations continue to belong exclusively to \`src/lowhangingfruitme\`. A simple **3% of hypothetical actually realized net recovery** pricing illustration is permitted on the public site, clearly marked as an example; it is not an audit, a recovery claim or an invoice.

## Implemented routes

| Page | Route | Scope |
|---|---|---|
| Startseite | \`/\` | Hero with original brand PNG, navigation, seven product-area cards with honest statuses, process flow, industry fit, 3%-example, FAQ and educational cards |
| Lieferantenboni | \`/lieferantenboni-pruefen\` | Rebate checking problem, source data and audit method |
| CFO / Marge | \`/margenanalyse\` | **Concept only** |
| Order-to-Cash | \`/auftragsautomatisierung\` | **Concept only** |
| Service Revenue | \`/serviceumsatz\` | **Concept only** |
| Wissen | \`/wissen\` | Five original educational articles with SEO metadata |
| Artikel | \`/wissen/[slug]\` | Five individual article routes |
| Bonusstaffeln | \`/bonusstaffeln-pruefen\` | Retrospective, marginal and fixed-threshold bonus models |
| Gutschriften | \`/bonusgutschriften-abgleichen\` | Source / period / contract matching |
| Preis & Ablauf | \`/preis-und-ablauf\` | Three-percent success-fee illustration and conditions |
| Eignungscheck | \`/eignungscheck\` | Minimum inputs and safe pilot contact instructions; no sensitive upload |
| Status | \`/status\` | Explicit separation of implemented capabilities and roadmap |
| Rechtliches | \`/impressum\`, \`/datenschutz\` | Incomplete staging text, **not** approved public legal notices |

The observed reference structure from the supplied 312-line DistroAgents report served as **navigation and information architecture only**. No reference text, logos, CSS or image assets are copied. Current public product statements follow the source repository, not the private DistroAgents backend or its marketing metrics.

## Branding – exact origin

\`portal/scripts/prepare-brand.mjs\` loads the actual original \`docs/Neon-Low-Hanging-FruitMe-Banner.png\`, measures representative sRGB pixels and writes a generated stylesheet \`portal/app/brand.generated.css\`, an unchanged image copy \`portal/public/neon-banner.png\`, and a provenance report \`portal/public/brand-measurement.json\`. These generated files are intentionally gitignored, but are included in build artifacts.

**Real GitHub CI observation:** source image 1983x793 pixels and SHA256 \`1525d2f792a9e5fd8aee4f564f34ba048b33fe37956204fff108f7b49f5b797c\`. A contrast ratio of at least 4.5 is required for the foreground/background tokens. Source pixel coordinates and actual HEX values are available in the per-build JSON; they are never guessed.

## CI acceptance and known limits

[GitHub Actions run 41586331503](https://github.com/tonnestate/LowHangingFruitMe/actions/runs/41586331503): completed/success on the code commit \`5f30a4bf0cd638e63c9fda53a9c3c19de0f8ed2f\`.

- 7 Node unit tests passed; fee half-up cents, original PNG source hash, sampled palette, launch protections.
- Next.js production/standalone build and TS typecheck passed.
- 12 Playwright Chromium tests passed across desktop 1440, tablet 768 and mobile 390: original banner rendered, navigation, FAQ interaction, 3% calculator, 404 and robots/noindex.
- Browser screenshots and measured brand JSON retained as CI artifacts.
- Real DistroAgents website visual baseline and exact responsive interactivity **not** independently measured, so **no pixel-perfect / 1:1 parity claim**.
- No accessible live website, no real IdP, no ERP connectors, no recovery ledger and no real lead intake.
- Future public release requires actual legal imprint/privacy policy, data minimization, fully configured contact method, independent security review and confirmation of public-domain/branding/legal rights.
- Site only claims 3% as a prospective commercial arrangement; legal review of agreement and attribution continues.

## Hosting contract

Deployment resources, templates and release gates: [\`portal/README.md\`](../portal/README.md), [\`deploy/apache-vhost.conf.example\`](../deploy/apache-vhost.conf.example), [\`deploy/lowhangingfruitme-portal.service.example\`](../deploy/lowhangingfruitme-portal.service.example).

Proposed dedicated service binds to \`127.0.0.1:3107\` behind Apache HTTPS on a **separate, not-yet-selected domain**. This is not a statement that the port is available or that the host can run Next.js yet; port use, Node version, CPU/memory, existing sites and installed Apache modules need actual pre-deployment inspection. Do not touch existing WordPress routes or database schemas.

A production deployment or public SEO indexing is **not** approved by the mere existence of this repo.

## Next action

Close the remaining infrastructure and legal prerequisites, then deploy staging for domain/TLS, security and real screenshot acceptance. Only after that, separately implement authenticated customer accounts, private file upload, verified source integration and the recovery ledger in the Python/API service.
