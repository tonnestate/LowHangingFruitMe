# Authenticated approval boundary – v0.6.0

**Status:** implemented as a Python resource-server authorization library and authenticated approval facade; no login UI, no live identity-provider registration, and no exposed HTTP endpoints.

## Architecture and trust boundaries

1. An external OAuth 2.0/OIDC authorization server issues a JWT **access token**, not an ID token, for the dedicated LowHangingFruitMe API audience. A server-side configured client-ID allowlist limits accepted OAuth clients.
2. `AccessTokenVerifier` verifies an RS256 signature against a **pre-provisioned trusted public JWKS**. The package never follows token-supplied `jku`, `x5u` or other URL hints, and does not dynamically fetch a JWKS. It verifies `typ=at+jwt` (RFC 9068), exact issuer, audience, timestamps, subject, token ID, client ID and a maximum token lifetime.
3. A successful signature yields an immutable `VerifiedPrincipal` (stable `sub` and verified scopes). Tenant/legal-entity values are **not** taken as authorization from token-supplied custom fields.
4. `AuthenticatedApprovalService` checks per-operation token scopes and an **active tenant/legal-entity reviewer grant in MariaDB**. It binds the HMAC receipt's reviewer ID to the token's verified subject and rejects false or unsupported principals.
5. `approve()` issues and registers a receipt on the server side; `revoke()` performs role-scoped atomic revocation.
6. `audit_csv()` requires the `lhfm:audit:execute` access scope and a live DB grant **before reading local source files**; after import it revalidates token validity and approval/reviewer grants inside the existing MariaDB `SELECT ... FOR UPDATE` dispatch interval. The initial vertical slice restricts execution to the reviewer who approved the contract.

## Required token and scopes

JWT access token profile: RFC 9068; asymmetric `RS256` only, trusted public RSA JWK with fixed `kid`, required `iss, aud, sub, exp, iat, nbf, jti, client_id`. Header `typ=at+jwt`. Token lifetime not greater than 3600 seconds. No fallback to unsigned JWT, HS256, ID token or dynamically fetched signing keys.

Operator scope mapping:

| Operation | Required JWT scope | Required MariaDB grant |
|---|---|---|
| `approve` | `lhfm:approval:write` | ACTIVE `contract_reviewer` for exact tenant/legal entity |
| `register` (internal migration/compatibility path) | `lhfm:approval:write` | Same grant and subject matching receipt |
| `revoke` | `lhfm:approval:revoke` | Same active grant |
| `audit_csv` | `lhfm:audit:execute` | Active original contract reviewer's grant, checked again at dispatch |

Scopes do not replace the database grant. Database grants do not replace verified identity.

## Configuration

For a trusted deployment, supply the following **outside the repository**:

- `LHFM_OIDC_ISSUER`: exact HTTPS issuer URL,
- `LHFM_OIDC_AUDIENCE`: unique resource/API audience,
- `LHFM_OIDC_JWKS_FILE`: trusted public JWKS JSON file readable only by the service,
- `LHFM_OIDC_ALLOWED_CLIENT_IDS`: comma-separated allowlist provisioned by the operator,
- `LHFM_APPROVAL_KEY_HEX`: separate backend-only HMAC secret, at least 32 bytes,
- `LHFM_DB_HOST / PORT / USER / PASSWORD / NAME`: dedicated MariaDB registry credentials.

There is no automatic issuer discovery or JWKS refresh. Rotation requires explicit trusted publication and reload; this prevents unknown runtime network fetches but is an operational limitation. If a supported IdP uses opaque tokens rather than RFC 9068 JWTs, this code is not compatible; do **not** accept them without a separate verified introspection design.

## Security and actual test evidence

`tests/test_auth.py` generates new 2048-bit RSA private keys **in test memory**, signs synthetic access tokens, and verifies: invalid signature, wrong issuer/audience/client/kid, ID token confusion, expired/oversized lifetime, required claims, forbidden key URLs and untrusted JWKS fields. Against a real isolated MariaDB, it tests authorized approval issuance, missing token, wrong subject, wrong tenant, insufficient access-token scopes, revoked receipt, accepted signed financial audit and token re-verification immediately before computation.

Existing tests additionally verify DB row-lock behavior during concurrent revocation. See [EVIDENCE.md](../EVIDENCE.md) for actual successful workflow run IDs. These tests do not prove connection to a commercial or user-selected IdP.

## Not yet implemented or verified

- No OpenID Connect browser authorization-code/PKCE login flow, session management, customer self-registration or administrator console.
- No real external IdP configuration, real reviewer account lifecycle, account deactivation or end-to-end secure data-access service.
- No JWKS rotation automation, token revocation/introspection, replay database, MFA enforcement or full audit of token issuance.
- No secured public HTTP API, tenant-protected object storage, malware-isolated upload or real customer data.
- No protected database grant-provisioning API: grants must be created by a separate authenticated administrative process.
- Low-level `ApprovalRegistry` and `issue_approval()` remain Python internals for trusted code and offline tests; they **must not be exposed** as customer endpoints with caller-supplied actor strings.

**Production release remains blocked** pending a real IdP tenant, hardened HTTP boundary, authentic provisioning, secure document registry, end-to-end and penetration tests, legal/compliance approval and recovery/billing implementation.


## Vertrauenswürdige JWKS-Dateirotation (04.11.2026 – CI bestanden)

Der file-basierte `AccessTokenVerifier` prüft die öffentliche JWKS-Datei nun **vor jeder Token-Verifikation** erneut auf reguläre Datei, No-Follow, Maximalgröße und SHA-256-Änderung. Nur vollständig validierte RS256-RSA-Public-Keys werden unter einem Lock atomar ersetzt. Ungültige/fehlende Dateien führen bis zur Korrektur zu verweigerter Authentifizierung; zuvor akzeptierte Schlüssel werden nach gültiger Rotation nicht stillschweigend weiter angenommen. Ein direkter `AccessTokenVerifier` mit explizit übergebenen Testschlüsseln bleibt unverändert. Weder issuer-Discovery noch externe JWKS-Netzabfragen, IdP-Provisioning oder Token-Refresh sind dadurch geschaffen. Die Datei muss von einem vertrauenswürdigen Betreiber atomar veröffentlicht und auf dem echten Host getestet werden.


**CI-Evidenz:** [Actions 41830627024](https://github.com/tonnestate/LowHangingFruitMe/actions/runs/41830627024), erfolgreich mit 338 Tests je Python 3.11/3.12, einschließlich Dateiwechsel, Widerruf eines alten KID, defekter Datei und Wiederherstellung. Die Race-Condition des gleichzeitigen JWKS-Snapshots wurde zusätzlich durch Serialisierung von Lesen/Validieren/Austauschen in [Commit 0aa7c0c](https://github.com/tonnestate/LowHangingFruitMe/commit/0aa7c0c5c8d2d163359538bc5644fce4013d1492) bereinigt. Keine Live-IdP-Abnahme.


## Serverseitige OIDC-Token-Rotation (04.11.2026)

Das geschützte Portal benötigt einen tatsächlichen HTTPS-Identity-Provider, einen Confidential-Client mit `refresh_token`, ein echtes `at+jwt` für die vom Python-Backend erwartete Audience sowie `AUTH_URL` und `AUTH_SECRET` (mindestens 32 Byte). Der feste `AUTH_OIDC_TOKEN_ENDPOINT` muss per HTTPS zur Issuer-Origin und deren Issuer-Pfad gehören. Tokens verbleiben im verschlüsselten HttpOnly/Secure/SameSite=Lax-Auth.js-JWE. Bei knapp abgelaufenem Access Token erneuert das BFF ihn durch begrenztes form-urlencoded POST ohne Weiterleitungen. Die JWE-Cookiefragmente werden bereinigt/neu geschrieben. Bei Refresh-Fehler wird die Browser-Sitzung geschlossen und eine neue Anmeldung erforderlich. Die Browser-Session-API liefert weiterhin keine Access-/Refresh-Credentials.

Eine Singleflight-Sperre verhindert gleichzeitige identische Refresh-Anfragen innerhalb einer Node-Instanz, **nicht** zwischen mehreren Prozessen. Es wurden weder ein echter OIDC-Provider installiert noch MFA, Benutzerentzug, Provider-Key-Rotation oder ein Lasttest auf dem VPS abgenommen. Entsprechende Go-Live-Gates bleiben offen.
