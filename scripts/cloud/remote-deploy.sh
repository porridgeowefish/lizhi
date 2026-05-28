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
REFRESH_ENQUEUE_SERVICE="${APP_NAME}-enqueue-refresh.service"
REFRESH_ENQUEUE_TIMER="${APP_NAME}-enqueue-refresh.timer"
REFRESH_WORKER_SERVICE="${APP_NAME}-refresh-worker.service"
REFRESH_WORKER_TIMER="${APP_NAME}-refresh-worker.timer"
CONTENT_WORKER_SERVICE="${APP_NAME}-content-worker.service"
CONTENT_WORKER_TIMER="${APP_NAME}-content-worker.timer"
LLM_WORKER_SERVICE="${APP_NAME}-llm-worker.service"
LLM_WORKER_TIMER="${APP_NAME}-llm-worker.timer"

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

write_worker_unit() {
  local service_name="$1"
  local description="$2"
  local lock_name="$3"
  local module_name="$4"
  local args="$5"

  cat >/etc/systemd/system/${service_name} <<EOF
[Unit]
Description=${description}
After=network.target ${SERVICE_NAME}

[Service]
Type=oneshot
WorkingDirectory=${CURRENT_DIR}/backend
EnvironmentFile=${REMOTE_ENV_PATH}
Environment=PYTHONPATH=${CURRENT_DIR}/backend
ExecStart=/usr/bin/flock -n -E 0 ${DATA_DIR}/locks/${lock_name}.lock ${CURRENT_DIR}/backend/.venv/bin/python -m ${module_name} --once ${args}
TimeoutStartSec=900
EOF
}

write_worker_timer() {
  local timer_name="$1"
  local service_name="$2"
  local description="$3"
  local first_delay="$4"
  local interval="$5"

  cat >/etc/systemd/system/${timer_name} <<EOF
[Unit]
Description=${description}

[Timer]
OnActiveSec=${first_delay}
OnUnitActiveSec=${interval}
AccuracySec=1min
Unit=${service_name}

[Install]
WantedBy=timers.target
EOF
}

write_worker_units() {
  mkdir -p "${DATA_DIR}/locks"

  write_worker_unit "${REFRESH_ENQUEUE_SERVICE}" "Campus Opportunity enqueue refresh jobs" "enqueue-refresh" "app.workers.enqueue_refresh_jobs" ""
  write_worker_timer "${REFRESH_ENQUEUE_TIMER}" "${REFRESH_ENQUEUE_SERVICE}" "Campus Opportunity enqueue refresh jobs timer" "5min" "60min"

  write_worker_unit "${REFRESH_WORKER_SERVICE}" "Campus Opportunity refresh worker" "refresh-worker" "app.workers.refresh_worker" "--limit 10"
  write_worker_timer "${REFRESH_WORKER_TIMER}" "${REFRESH_WORKER_SERVICE}" "Campus Opportunity refresh worker timer" "6min" "2min"

  write_worker_unit "${CONTENT_WORKER_SERVICE}" "Campus Opportunity content worker" "content-worker" "app.workers.content_worker" "--limit 5"
  write_worker_timer "${CONTENT_WORKER_TIMER}" "${CONTENT_WORKER_SERVICE}" "Campus Opportunity content worker timer" "8min" "2min"

  write_worker_unit "${LLM_WORKER_SERVICE}" "Campus Opportunity LLM worker" "llm-worker" "app.workers.llm_worker" "--limit 2"
  write_worker_timer "${LLM_WORKER_TIMER}" "${LLM_WORKER_SERVICE}" "Campus Opportunity LLM worker timer" "10min" "5min"
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
BACKEND_POST_FETCH_LIMIT=500
BACKEND_INCREMENTAL_POST_FETCH_LIMIT=100
BACKEND_SOURCE_FETCH_LIMIT=500
BACKEND_ENABLE_SCHEDULER=false
BACKEND_UPSTREAM_REFRESH_ENABLED=true
BACKEND_UPSTREAM_REFRESH_ON_STARTUP=false
BACKEND_UPSTREAM_REFRESH_INTERVAL_MINUTES=60
BACKEND_UPSTREAM_REFRESH_START_PAGE=0
BACKEND_UPSTREAM_REFRESH_END_PAGE=10
BACKEND_UPSTREAM_REFRESH_REQUEST_DELAY_SECONDS=1.0
BACKEND_UPSTREAM_REFRESH_SETTLE_SECONDS=300
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
BACKEND_LLM_QUEUE_ENABLED=false
BACKEND_LLM_WORKER_INTERVAL_SECONDS=20
BACKEND_LLM_WORKER_BATCH_SIZE=2
BACKEND_LLM_WORKER_MAX_ATTEMPTS=3
BACKEND_CONTENT_WORKER_BATCH_SIZE=5
BACKEND_QUEUE_RECENT_DAYS=30
BACKEND_HOMEPAGE_RECENT_UNDATED_DAYS=90
EOF
    echo "Created ${REMOTE_ENV_PATH}. Fill in upstream and LLM credentials before syncing production data."
  fi
  ensure_min_int_env BACKEND_POST_FETCH_LIMIT 500
  ensure_env_default BACKEND_INCREMENTAL_POST_FETCH_LIMIT 100
  ensure_min_int_env BACKEND_SOURCE_FETCH_LIMIT 500
  set_env_value BACKEND_ENABLE_SCHEDULER false
  ensure_bool_env BACKEND_UPSTREAM_REFRESH_ENABLED true
  set_env_value BACKEND_UPSTREAM_REFRESH_ON_STARTUP false
  ensure_min_int_env BACKEND_UPSTREAM_REFRESH_INTERVAL_MINUTES 60
  ensure_env_default BACKEND_UPSTREAM_REFRESH_START_PAGE 0
  ensure_min_int_env BACKEND_UPSTREAM_REFRESH_END_PAGE 10
  ensure_env_default BACKEND_UPSTREAM_REFRESH_REQUEST_DELAY_SECONDS 1.0
  ensure_min_int_env BACKEND_UPSTREAM_REFRESH_SETTLE_SECONDS 300
  set_env_value BACKEND_LLM_QUEUE_ENABLED false
  ensure_min_int_env BACKEND_LLM_WORKER_INTERVAL_SECONDS 20
  ensure_max_int_env BACKEND_LLM_WORKER_BATCH_SIZE 2
  ensure_min_int_env BACKEND_LLM_WORKER_MAX_ATTEMPTS 3
  ensure_min_int_env BACKEND_CONTENT_WORKER_BATCH_SIZE 5
  ensure_env_default BACKEND_QUEUE_RECENT_DAYS 30
  ensure_env_default BACKEND_HOMEPAGE_RECENT_UNDATED_DAYS 90
}

set_env_value() {
  local key="$1"
  local value="$2"
  if grep -q "^${key}=" "${REMOTE_ENV_PATH}"; then
    sed -i "s#^${key}=.*#${key}=${value}#" "${REMOTE_ENV_PATH}"
  else
    printf '\n%s=%s\n' "${key}" "${value}" >>"${REMOTE_ENV_PATH}"
  fi
}

ensure_min_int_env() {
  local key="$1"
  local minimum="$2"
  local current=""
  current="$(grep -E "^${key}=" "${REMOTE_ENV_PATH}" | tail -n 1 | cut -d= -f2- || true)"
  if [[ ! "${current}" =~ ^[0-9]+$ ]] || (( current < minimum )); then
    set_env_value "${key}" "${minimum}"
  fi
}

ensure_max_int_env() {
  local key="$1"
  local maximum="$2"
  local current=""
  current="$(grep -E "^${key}=" "${REMOTE_ENV_PATH}" | tail -n 1 | cut -d= -f2- || true)"
  if [[ ! "${current}" =~ ^[0-9]+$ ]] || (( current > maximum )); then
    set_env_value "${key}" "${maximum}"
  fi
}

ensure_env_default() {
  local key="$1"
  local value="$2"
  if ! grep -q "^${key}=" "${REMOTE_ENV_PATH}"; then
    set_env_value "${key}" "${value}"
  fi
}

ensure_bool_env() {
  local key="$1"
  local value="$2"
  local current=""
  current="$(grep -E "^${key}=" "${REMOTE_ENV_PATH}" | tail -n 1 | cut -d= -f2- || true)"
  if [[ -z "${current}" ]]; then
    set_env_value "${key}" "${value}"
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
write_worker_units
write_nginx_config

systemctl daemon-reload
systemctl enable "${SERVICE_NAME}"
systemctl restart "${SERVICE_NAME}"
systemctl enable --now "${REFRESH_ENQUEUE_TIMER}"
systemctl enable --now "${REFRESH_WORKER_TIMER}"
systemctl enable --now "${CONTENT_WORKER_TIMER}"
systemctl enable --now "${LLM_WORKER_TIMER}"
systemctl enable nginx
nginx -t
systemctl restart nginx

sleep 2
curl -fsS http://127.0.0.1:8002/api/health >/dev/null
curl -fsS "http://127.0.0.1:8002/api/posts?limit=1" >/dev/null
rm -rf "${TMP_DIR}"
echo "Remote deploy completed successfully."
