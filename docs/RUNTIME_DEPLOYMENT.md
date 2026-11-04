# LowHangingFruitMe – private API and portal runtime integration (v0.17)

Status: **SOURCE AND STARTUP GATE IMPLEMENTED; TARGET VPS NOT INSTALLED OR VERIFIED**.

The actual service factory, `create_app_from_environment()`, now performs
the same read-only live runtime gate as the dedicated
`lhfm-runtime-check` operator command. No API server is constructed
with an unsecured upload/source root, an incomplete SQL 001–010 ledger,
unreachable local ClamAV, absent trusted public JWKS, or failed Docling
network-isolation preflight. The injected `create_app(...)` constructor
is for synthetic unit tests and does not replace this factory.

## Process and trust boundaries

- Apache is the **only** public webserver on TLS port 443 and proxies the
  existing Next.js standalone application on **127.0.0.1:3107**.
  `deploy/apache-vhost.conf.example` remains an operator-reviewed example;
  no existing live Apache or WordPress virtual host is modified.
- The portal is operated by the existing dedicated `lowhangingfruitme`
  account. The confidential root-owned 0600 EnvironmentFile
  `/etc/lowhangingfruitme/portal.env` holds real OIDC client registration,
  `AUTH_URL=https://YOUR_REAL_HOST`, a persistent strong `AUTH_SECRET`,
  and `LHFM_API_INTERNAL_URL=http://127.0.0.1:8127`. It must not
  contain the API HMAC key or private SQL credentials.
- The FastAPI process uses a **separate unprivileged `lhfm-api` account**
  and an exclusively local **127.0.0.1:8127** listener. The root-owned 0600
  `/etc/lowhangingfruitme/api.env` is loaded by systemd, not placed in
  public web directories. The API service's `ExecStartPre` runs the
  operator-check command; the Python application factory independently
  refuses bootstrap if any gate fails. Root execution is rejected.
- Both private input trees are outside the Apache document root, owned by
  `lhfm-api`, mode **0700**, with no symlink path components and
  no overlapping ancestors. The upload root stores scanned client files.
  The audit/source root MUST also be writable for the controlled,
  append-only reviewed bundle promotion; it must **not** be exported or
  exposed as static content. Neither the portal nor Apache must run
  with the `lhfm-api` UID.
- MariaDB is local on 127.0.0.1. The API DB credential should have only
  the necessary runtime DML and metadata privileges on its own schema;
  do not grant runtime CREATE/ALTER/DROP. Migration maintenance is
  separately approved and requires backed-up, checksum-pinned SQL.
- The file at `LHFM_OIDC_JWKS_FILE` contains **only public RSA JWKS**
  from the real configured IdP. The operator publishes it atomically.
  The IdP and actual `at+jwt` audience/client claims must be externally
  checked. The API's persistent HMAC key must not be regenerated on
  every restart.
- ClamAV must provide a real LOCAL UNIX socket accessible to `lhfm-api`
  with current signatures. Its daemon and socket permissions are an
  external installation task; do not bypass the scanner to pass readiness.
- The root-controlled `LHFM_DOCLING_SANDBOX_LAUNCHER` must be an
  operator-installed, executable, offline Bubblewrap profile with separate
  network namespace and only loopback interface. The code probes it;
  this does not certify a real OCR benchmark or full OS process sandbox.

## Host preparation (not performed from this chat)

1. Identify a compatible VPS OS, installed runtime binaries, backup policy,
   existing Apache TLS domains and WordPress vhosts. Do not overwrite
   existing vhosts; use a **new confirmed domain and reviewed vhost**.
2. Provision `lhfm-api` as a dedicated system UID, not root and not the
   portal/Apache user. Prepare
   `/var/lib/lowhangingfruitme/private-sources` and
   `/var/lib/lowhangingfruitme/private-uploads` as `lhfm-api`-owned
   0700 directories. Both are writable only to that UID.
3. Install the reviewed Python wheel with
   `[import,registry,auth,universal,api]` and the Next.js standalone
   build under `/srv/lowhangingfruitme/`. Supply offline Docling
   dependencies and local model files and verify the actual root-owned
   executable sandbox launcher (see `docs/DOCLING_SANDBOX.md`).
4. Populate `/etc/lowhangingfruitme/api.env` from
   `deploy/api.env.example` with **real secrets out of Git** and
   operator-provisioned OIDC public JWKS. Place the portal's separate
   `portal.env` alongside it. Both must be root-owned 0600.
   The portal environment schema is in `portal/.env.example`.
5. Apply pinned SQL migrations 001–010 from the controlled operator
   procedure only after a verified encrypted backup. Run
   `lhfm-schema-check`, then `lhfm-runtime-check` **as the service UID**
   with the same systemd-loaded API environment.
6. Review and adapt the two templates
   `deploy/lowhangingfruitme-api.service.example` and
   `deploy/lowhangingfruitme-portal.service.example`. Verify syntax
   with `systemd-analyze verify`, installed python and node paths,
   local port availability, filesystem/ClamAV permissions and actual
   sandbox behavior. Then install in systemd and enable both only
   after operator approval.
7. For Apache use the reviewed HTTPS-only proxy example. Ensure **8127
   and 3107 are bound ONLY to 127.0.0.1 and not open in the firewall**.
   `--no-proxy-headers` rejects untrusted forwarding metadata at the
   financial API. The BFF retains the only permitted internal API proxy
   allowlist and performs its own authenticated session checks.

## Local acceptance probes on the actual host

After validated service start (never claim they ran from CI):

```bash
sudo systemctl status lowhangingfruitme-api lowhangingfruitme-portal
ss -lntp
curl --silent --show-error --fail http://127.0.0.1:8127/healthz
curl --silent --show-error --fail http://127.0.0.1:8127/readyz
curl --silent --show-error -i http://127.0.0.1:8127/v1/me
curl --silent --show-error --fail --head http://127.0.0.1:3107/
```

Require: local liveness and readiness respond without privileged input,
private `/v1/me` returns HTTP 401 without a valid bearer, no other
addresses listen on either internal service port. Then verify HTTPS
certificate chain, actual IdP login, expired-token refresh, revoked
tokens, tenant grant enforcement, ClamAV infected/clean samples,
Docling offline/egress-denial and end-to-end financial test with a
separately accepted actual business sample. Do **not** interpret
`/healthz` or `systemctl active` as a substitute for `/readyz`.

## Explicit remaining gates

This release contains neither a working VPS installation nor a live
OIDC provider registration, commercial invoicing, independently reviewed
ERP data, legally approved client contract or operating-recovery RPO/RTO.
No existing Apache vhost, customer database or document archive has been
touched. Synthetic CI plus a service template is **not** production
approval. See `docs/GO_LIVE_GATE.md` (G0–G5).


## Offline-Wartungsbefehl für abgebrochene Uploads (v0.18)

Nach genehmigtem Wartungsfenster und überprüftem Stopp sämtlicher
API-/Upload-Worker ist `lhfm-upload-housekeeping` als separate
unprivilegierte CLI installierbar; **kein automatischer Timer** und
keine neue öffentliche HTTP-Route. Der Operator muss erst die
Vorschau prüfen und dann beide Apply-Freigaben vorhalten. Die
Datensätze und Prüfschritte sind im
`docs/UPLOAD_HOUSEKEEPING.md` dokumentiert.


## Abgesicherte BFF-Antworten und Docling-Zeitbudget (04.11.2026)

Die Next.js-BFF-Grenze begrenzt eingehende Backend-Antworten während des Streamings auf 4 MiB statt erst nach vollständiger Pufferung. Ein zu großes oder ungültiges Content-Length sowie ein überlaufender Chunk-Stream werden mit HTTP 502 abgelehnt; binäre Report-Bytes bleiben unverändert. Für POST /v1/contract-candidates gelten 135 Sekunden BFF-Timeout wegen des 120-Sekunden-Docling-Workerlimits. Die Apache-VirtualHost-Vorlage platziert daher /api/finance/ mit 150 Sekunden vor dem allgemeinen 45-Sekunden-Website-Proxy. Der Runtime-Host muss diese Template-Reihenfolge und die tatsächlichen Netzwerk-/Proxy-Zeitlimits separat prüfen. Eine synchrone HTTP-Langzeitverarbeitung ist keine persistente Jobqueue; Neustart-, Wiederaufnahme- und Lasttests auf dem VPS bleiben offen.
