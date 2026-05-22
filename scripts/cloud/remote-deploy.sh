#!/usr/bin/env bash
set -euo pipefail

PACKAGE_PATH="${1:?package path required}"
TARGET_DIR="${TARGET_DIR:-/opt/campus-opportunity}"
REMOTE_ENV_PATH="${REMOTE_ENV_PATH:-/etc/campus-opportunity/backend.env}"
DOMAIN="${DOMAIN:-_}"
APP_NAME="campus-opportunity"
CURRENT_DIR="${TARGET_DIR}/current"
TMP_DIR="${TARGET_DIR}/tmp-extract"
DATA_DIR="/var/lib/${APP_NAME}"
SERVICE_NAME="${APP_NAME}-backend.service"

need_cmd() {
  command -v "$1" >/dev/null 2>&1
}

install_base_packages() {
  if need_cmd apt-get; then
    apt-get update
    apt-get install -y python3 python3-venv python3-pip nginx
  elif need_cmd dnf; then
    dnf install -y python3 python3-pip nginx
  elif need_cmd yum; then
    yum install -y python3 python3-pip nginx
  else
    echo "Unsupported package manager. Please install python3, python3-venv, python3-pip, and nginx manually." >&2
    exit 1
  fi
}

write_backend_service() {
  cat >/etc/systemd/system/${SERVICE_NAME} <<EOF
[Unit]
Description=Campus Opportunity Backend
After=network.target

[Service]
Type=simple
WorkingDirectory=${CURRENT_DIR}/backend
EnvironmentFile=${REMOTE_ENV_PATH}
Environment=PYTHONPATH=${CURRENT_DIR}/backend
ExecStart=${CURRENT_DIR}/backend/.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8002
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF
}

write_nginx_config() {
  local conf_path=""
  if [[ -d /etc/nginx/conf.d ]]; then
    conf_path="/etc/nginx/conf.d/${APP_NAME}.conf"
  else
    conf_path="/etc/nginx/sites-available/${APP_NAME}"
  fi

  cat >"${conf_path}" <<EOF
server {
    listen 80;
    server_name ${DOMAIN};

    root ${CURRENT_DIR}/frontend/dist;
    index index.html;

    location /api/ {
        proxy_pass http://127.0.0.1:8002/api/;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location / {
        try_files \$uri \$uri/ /index.html;
    }
}
EOF

  if [[ -d /etc/nginx/sites-enabled ]]; then
    ln -sf "${conf_path}" "/etc/nginx/sites-enabled/${APP_NAME}"
    rm -f /etc/nginx/sites-enabled/default || true
  fi
}

ensure_env_file() {
  mkdir -p "$(dirname "${REMOTE_ENV_PATH}")"
  mkdir -p "${DATA_DIR}"
  if [[ ! -f "${REMOTE_ENV_PATH}" ]]; then
    cat >"${REMOTE_ENV_PATH}" <<EOF
BACKEND_HOST=127.0.0.1
BACKEND_PORT=8002
BACKEND_DATABASE_URL=sqlite:///${DATA_DIR}/backend.db
BACKEND_SYNC_INTERVAL_MINUTES=10
BACKEND_POST_FETCH_LIMIT=50
BACKEND_SOURCE_FETCH_LIMIT=200
BACKEND_ENABLE_SCHEDULER=true
BACKEND_UPSTREAM_BASE_URL=
BACKEND_UPSTREAM_USERNAME=
BACKEND_UPSTREAM_PASSWORD=
BACKEND_LLM_ENABLED=false
BACKEND_LLM_BASE_URL=
BACKEND_LLM_API_KEY=
BACKEND_LLM_MODEL=
BACKEND_LLM_TIMEOUT_SECONDS=30
BACKEND_LLM_PROMPT_VERSION=iter1-v1
BACKEND_LLM_MAX_INPUT_CHARS=6000
EOF
    echo "Created ${REMOTE_ENV_PATH}. Fill in upstream and LLM credentials before syncing production data."
  fi
  if ! grep -q '^BACKEND_POST_FETCH_LIMIT=' "${REMOTE_ENV_PATH}"; then
    printf '\nBACKEND_POST_FETCH_LIMIT=50\n' >>"${REMOTE_ENV_PATH}"
  fi
}

install_base_packages
mkdir -p "${TARGET_DIR}"
rm -rf "${TMP_DIR}"
mkdir -p "${TMP_DIR}"
tar -xzf "${PACKAGE_PATH}" -C "${TMP_DIR}"

rm -rf "${CURRENT_DIR}"
mkdir -p "${CURRENT_DIR}/backend" "${CURRENT_DIR}/frontend"
cp -R "${TMP_DIR}/backend/app" "${CURRENT_DIR}/backend/app"
cp "${TMP_DIR}/backend/requirements.txt" "${CURRENT_DIR}/backend/requirements.txt"
cp "${TMP_DIR}/backend/README.md" "${CURRENT_DIR}/backend/README.md"
cp -R "${TMP_DIR}/frontend/dist" "${CURRENT_DIR}/frontend/dist"
find "${CURRENT_DIR}" -type d -name '__pycache__' -prune -exec rm -rf {} +
find "${CURRENT_DIR}" -type f \( -name '*.pyc' -o -name '*.pyo' -o -name '*.db' -o -name '*.sqlite' \) -delete

python3 -m venv "${CURRENT_DIR}/backend/.venv"
"${CURRENT_DIR}/backend/.venv/bin/pip" install --upgrade pip
"${CURRENT_DIR}/backend/.venv/bin/pip" install -r "${CURRENT_DIR}/backend/requirements.txt"

ensure_env_file
write_backend_service
write_nginx_config

systemctl daemon-reload
systemctl enable "${SERVICE_NAME}"
systemctl restart "${SERVICE_NAME}"
systemctl enable nginx
nginx -t
systemctl restart nginx

sleep 2
curl -fsS http://127.0.0.1:8002/api/health >/dev/null
curl -fsS "http://127.0.0.1:8002/api/posts?limit=1" >/dev/null
if grep -q '^BACKEND_UPSTREAM_BASE_URL=.' "${REMOTE_ENV_PATH}" \
  && grep -q '^BACKEND_UPSTREAM_USERNAME=.' "${REMOTE_ENV_PATH}" \
  && grep -q '^BACKEND_UPSTREAM_PASSWORD=.' "${REMOTE_ENV_PATH}"; then
  curl -fsS -X POST http://127.0.0.1:8002/api/sync >/tmp/${APP_NAME}-sync-smoke.json
  python3 - <<'PY'
import json
from pathlib import Path
payload = json.loads(Path("/tmp/campus-opportunity-sync-smoke.json").read_text())
if payload.get("status") not in {"completed", "partial_failed"}:
    raise SystemExit(f"sync smoke failed: {payload.get('status')} {payload.get('error_summary')}")
PY
fi

rm -rf "${TMP_DIR}"
echo "Remote deploy completed successfully."
