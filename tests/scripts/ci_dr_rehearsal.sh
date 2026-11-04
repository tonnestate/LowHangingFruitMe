#!/usr/bin/env bash
# GitHub Actions only: synthetic MariaDB + files, an ephemeral age keypair.
set -Eeuo pipefail
umask 077
test "$LHFM_DB_NAME" = "lhfm_test"
scratch="$(mktemp -d /tmp/lhfm-dr-ci-XXXXXXXX)"
trap 'rm -rf "$scratch"' EXIT
mkdir -m 700 "$scratch/uploads" "$scratch/sources"
printf 'Synthetic contract for encrypted DR regression.\n' > "$scratch/uploads/contract.pdf"
mkdir -m 700 "$scratch/sources/case"
printf '{"synthetic":true,"fee_due_net":"0.00"}\n' > "$scratch/sources/case/audit.json"
chmod 600 "$scratch/uploads/contract.pdf" "$scratch/sources/case/audit.json"
cat > "$scratch/client.cnf" <<'CNF'
[client]
host=127.0.0.1
port=3306
user=lhfm
password=testing-user-only
protocol=tcp
CNF
chmod 600 "$scratch/client.cnf"
age-keygen -o "$scratch/identity" >/dev/null 2>&1
chmod 600 "$scratch/identity"
recipient="$(age-keygen -y "$scratch/identity")"
test -n "$recipient"

# The service-created lhfm account has only the synthetic lhfm_test database.
# Create a separately scoped, empty disposable destination as root.
MYSQL_PWD=testing-root-only mariadb --host=127.0.0.1 --user=root \
  --execute="CREATE DATABASE lhfm_restore_ci; GRANT ALL ON lhfm_restore_ci.* TO 'lhfm'@'%'; FLUSH PRIVILEGES;"

# A CI-only non-empty sample row makes a zero-row restore insufficient.
LHFM_MAINTENANCE_CONFIRMED=YES python -m lowhangingfruitme.dr backup \
  --defaults-file "$scratch/client.cnf" --database lhfm_test \
  --upload-root "$scratch/uploads" --source-root "$scratch/sources" \
  --destination "$scratch/snapshot" --age-recipient "$recipient" \
  > "$scratch/backup-result.json"
test "$(find "$scratch/snapshot" -type f | wc -l)" -eq 4
test "$(find "$scratch/snapshot" -type f ! -name '*.age' | wc -l)" -eq 0

LHFM_RESTORE_REHEARSAL_APPROVED=YES python -m lowhangingfruitme.dr restore-verify \
  --defaults-file "$scratch/client.cnf" --backup-dir "$scratch/snapshot" \
  --age-identity "$scratch/identity" --target-database lhfm_restore_ci \
  > "$scratch/restore-result.json"
python - "$scratch/restore-result.json" <<'PY'
import json,sys
result=json.load(open(sys.argv[1],encoding="utf-8"))
assert result["restore_verified"] is True
assert result["table_counts_match"] is True
assert result["upload_files_checked"] == 1
assert result["audit_source_files_checked"] == 1
assert result["invoice_created"] is False
print("DR_SYNTHETIC_RESTORE_VERIFIED")
PY

# Replaying into a nonempty DB must fail before any SQL is imported.
if LHFM_RESTORE_REHEARSAL_APPROVED=YES python -m lowhangingfruitme.dr restore-verify \
  --defaults-file "$scratch/client.cnf" --backup-dir "$scratch/snapshot" \
  --age-identity "$scratch/identity" --target-database lhfm_restore_ci \
  > /dev/null 2>&1; then
  echo "unsafe repeated restore accepted" >&2
  exit 2
fi

# Failed encrypted archive digest is detected BEFORE any restore attempt.
printf X >> "$scratch/snapshot/uploads.tar.age"
MYSQL_PWD=testing-root-only mariadb --host=127.0.0.1 --user=root \
  --execute="CREATE DATABASE lhfm_restore_corrupt; GRANT ALL ON lhfm_restore_corrupt.* TO 'lhfm'@'%';"
if LHFM_RESTORE_REHEARSAL_APPROVED=YES python -m lowhangingfruitme.dr restore-verify \
  --defaults-file "$scratch/client.cnf" --backup-dir "$scratch/snapshot" \
  --age-identity "$scratch/identity" --target-database lhfm_restore_corrupt \
  > /dev/null 2>&1; then
  echo "tampered ciphertext accepted" >&2
  exit 2
fi
echo "DR_FAILURE_GATES_PASSED"
