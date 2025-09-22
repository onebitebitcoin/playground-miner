#!/usr/bin/env bash

set -euo pipefail

# Playground Miner test deployment script (Ubuntu)
# Based on deploy.sh, adapted for test environment.
#
# Usage:
#   SERVER_NAME=test.onebitebitcoin.com BACKEND_PORT=8003 sudo -E ./test_deploy.sh
#
# Notes:
# - Expects Ubuntu with apt. Installs Node LTS, Python, Nginx.
# - Backend (Django) runs via systemd + gunicorn on 127.0.0.1:$BACKEND_PORT.
# - Frontend (Vite) is built and served by Nginx from /var/www/test.

PROJECT_NAME="test"
ROOT_DIR=$(pwd)
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"
FRONTEND_DEPLOY_DIR="/var/www/${PROJECT_NAME}"
SERVICE_NAME="${PROJECT_NAME}-backend"
BACKEND_PORT="${BACKEND_PORT:-8003}"
# Default to the intended domain; override via SERVER_NAME env
SERVER_NAME="${SERVER_NAME:-test.onebitebitcoin.com}"

echo "=== Deploying $PROJECT_NAME ==="
echo "Root: $ROOT_DIR"
echo "Backend: $BACKEND_DIR"
echo "Frontend: $FRONTEND_DIR"
echo "Deploy dir: $FRONTEND_DEPLOY_DIR"
echo "Service: $SERVICE_NAME on 127.0.0.1:$BACKEND_PORT"
echo "Server name: $SERVER_NAME"

echo "Updating system packages..."
sudo apt update -y && sudo apt upgrade -y

echo "Installing dependencies (Python, Node LTS, Nginx, tools)..."
sudo apt install -y curl wget git build-essential software-properties-common \
  python3 python3-pip python3-venv psmisc net-tools

if ! command -v node >/dev/null 2>&1; then
  echo "Installing Node.js LTS..."
  curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
  sudo apt install -y nodejs
fi

if ! command -v nginx >/dev/null 2>&1; then
  echo "Installing Nginx..."
  sudo apt install -y nginx
  sudo systemctl enable nginx
  sudo systemctl start nginx
fi

if command -v ufw >/dev/null 2>&1; then
  echo "Configuring UFW..."
  sudo ufw allow ssh || true
  sudo ufw allow 'Nginx Full' || true
  sudo ufw --force enable || true
fi

echo "Preparing frontend deploy directory..."
sudo mkdir -p "$FRONTEND_DEPLOY_DIR"
sudo chown -R "$USER":"$USER" "$FRONTEND_DEPLOY_DIR"

echo "=== Backend: Django setup ==="
if [ -f "$BACKEND_DIR/requirements.txt" ]; then
  cd "$BACKEND_DIR"
  echo "Creating Python virtualenv..."
  python3 -m venv venv
  source venv/bin/activate

  echo "Installing Python dependencies..."
  pip install --upgrade pip
  pip install -r requirements.txt
  pip install gunicorn

  echo "Checking for missing migrations..."
  if ! python manage.py makemigrations --check --dry-run; then
    echo "\nERROR: There are model changes without migrations.\n"
    echo "Run 'python manage.py makemigrations' locally, commit, and redeploy."
    exit 1
  fi

  echo "Running migrations..."
  python manage.py migrate --noinput

  echo "Seeding initial data (fees, services, mnemonics) if empty..."
  python init_defaults.py || true

  echo "Collecting static files (best-effort)..."
  # collectstatic may be skipped if STATIC_ROOT isn't configured; ignore failures
  python manage.py collectstatic --noinput || true

  echo "Copying staticfiles and media to deploy directory (if present)..."
  sudo mkdir -p "$FRONTEND_DEPLOY_DIR/staticfiles"
  if [ -d "$BACKEND_DIR/staticfiles" ]; then
    sudo cp -r "$BACKEND_DIR/staticfiles/"* "$FRONTEND_DEPLOY_DIR/staticfiles/" 2>/dev/null || true
  fi
  if [ -d "$ROOT_DIR/staticfiles" ]; then
    sudo cp -r "$ROOT_DIR/staticfiles/"* "$FRONTEND_DEPLOY_DIR/staticfiles/" 2>/dev/null || true
  fi
  sudo mkdir -p "$FRONTEND_DEPLOY_DIR/media"
  if [ -d "$ROOT_DIR/media" ]; then
    sudo cp -r "$ROOT_DIR/media/"* "$FRONTEND_DEPLOY_DIR/media/" 2>/dev/null || true
  fi
  # Ensure permissions are consistent after copying
  sudo chown -R www-data:www-data "$FRONTEND_DEPLOY_DIR"/
  sudo chmod -R 755 "$FRONTEND_DEPLOY_DIR"/

  # Optional: create a superuser automatically (disabled by default)
  # python manage.py shell -c "\
  # from django.contrib.auth import get_user_model; U=get_user_model(); \
  # U.objects.filter(username='admin').exists() or U.objects.create_superuser('admin','admin@example.com','admin123')"

  deactivate
else
  echo "requirements.txt not found in $BACKEND_DIR; skipping backend setup"
fi

echo "=== Frontend: Build and deploy ==="
if [ -f "$FRONTEND_DIR/package.json" ]; then
  cd "$FRONTEND_DIR"
  echo "Installing Node dependencies..."
  npm ci || npm install

  echo "Building production build..."
  npm run build

  echo "Deploying to $FRONTEND_DEPLOY_DIR..."
  sudo rm -rf "$FRONTEND_DEPLOY_DIR"/*
  sudo cp -r dist/. "$FRONTEND_DEPLOY_DIR"/
  sudo chown -R www-data:www-data "$FRONTEND_DEPLOY_DIR"/
  sudo chmod -R 755 "$FRONTEND_DEPLOY_DIR"/
else
  echo "package.json not found in $FRONTEND_DIR; skipping frontend build"
fi

echo "=== systemd: Backend service ==="
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
# Ensure persistent secrets directory and encryption key
SECRETS_DIR="/etc/${PROJECT_NAME}"
sudo mkdir -p "$SECRETS_DIR"
KEY_FILE="$SECRETS_DIR/mnemonic.key"
if [ ! -f "$KEY_FILE" ]; then
  echo "Generating persistent MNEMONIC_ENCRYPTION_KEY..."
  KEY=$(python - <<'PY'
from cryptography.fernet import Fernet
print(Fernet.generate_key().decode())
PY
)
  echo "$KEY" | sudo tee "$KEY_FILE" >/dev/null
  sudo chmod 600 "$KEY_FILE"
else
  KEY=$(sudo cat "$KEY_FILE")
fi
sudo tee "$SERVICE_FILE" >/dev/null <<EOF
[Unit]
Description=$PROJECT_NAME Django Backend
After=network.target

[Service]
Type=simple
User=$USER
Group=www-data
WorkingDirectory=$BACKEND_DIR
Environment="PATH=$BACKEND_DIR/venv/bin:/usr/local/bin:/usr/bin:/bin"
Environment="PYTHONPATH=$BACKEND_DIR"
Environment="DJANGO_SETTINGS_MODULE=playground_server.settings"
Environment="ALLOWED_HOSTS=${SERVER_NAME},localhost,127.0.0.1"
Environment="MNEMONIC_ENCRYPTION_KEY=$KEY"
Environment="INIT_TOKEN=0000"
ExecStart=$BACKEND_DIR/venv/bin/gunicorn \
  --workers ${GUNICORN_WORKERS:-2} \
  --worker-class uvicorn.workers.UvicornWorker \
  --timeout ${GUNICORN_TIMEOUT:-60} \
  --keep-alive ${GUNICORN_KEEPALIVE:-5} \
  --bind 127.0.0.1:$BACKEND_PORT \
  playground_server.asgi:application
ExecReload=/bin/kill -s HUP \$MAINPID
KillMode=mixed
TimeoutStopSec=5
TimeoutStartSec=30
PrivateTmp=true
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable "$SERVICE_NAME"

echo "Stopping existing backend service if running..."
sudo systemctl stop "$SERVICE_NAME" 2>/dev/null || true

echo "Killing any existing processes on port $BACKEND_PORT and stray gunicorn/uvicorn..."
sudo fuser -k "$BACKEND_PORT"/tcp 2>/dev/null || true
sudo pkill -f "gunicorn.*playground_server" 2>/dev/null || true
sudo pkill -f "uvicorn.*playground_server" 2>/dev/null || true

echo "Starting backend service (gunicorn via systemd)..."
sudo systemctl start "$SERVICE_NAME" || true

sleep 3
if sudo systemctl is-active --quiet "$SERVICE_NAME"; then
  echo "✅ Backend service is active"
  # Quick health check
  if curl -fsS "http://127.0.0.1:$BACKEND_PORT/api/status" >/dev/null 2>&1; then
    echo "✅ Backend health check passed"
  else
    echo "⚠️ Backend health check failed; recent logs:"
    sudo journalctl -u "$SERVICE_NAME" -n 50 --no-pager || true
  fi
else
  echo "⚠️ Backend service failed to start; attempting manual gunicorn start"
  cd "$BACKEND_DIR"
  source venv/bin/activate
  sudo fuser -k "$BACKEND_PORT"/tcp 2>/dev/null || true
  nohup "$BACKEND_DIR/venv/bin/gunicorn" --workers 3 --bind 127.0.0.1:"$BACKEND_PORT" playground_server.wsgi:application \
    > /var/log/${PROJECT_NAME}-gunicorn.log 2>&1 &
  deactivate
fi

echo "=== Nginx: Reverse proxy + static ==="
# Name the nginx config after the server_name (e.g., test.onebitebitcoin.com.conf)
CERT_DOMAIN="${CERT_DOMAIN:-onebitebitcoin.com}"
NGINX_BASENAME="${SERVER_NAME:-$PROJECT_NAME}"
NGINX_CONF="/etc/nginx/sites-available/${NGINX_BASENAME}.conf"

# ACME challenge directory (for certbot)
sudo mkdir -p /var/www/letsencrypt

# Write nginx configuration referencing training script style (HTTP->HTTPS + SSL site)
sudo bash -c "cat > '$NGINX_CONF'" <<EOF
server {
    listen 80;
    server_name $SERVER_NAME;

    location ~ /.well-known/acme-challenge/ {
        root /var/www/letsencrypt;
        allow all;
        try_files \$uri =404;
    }

    location / {
        return 301 https://\$host\$request_uri;
    }
}

server {
    listen 443 ssl http2;
    server_name $SERVER_NAME;

    access_log /var/log/nginx/${NGINX_BASENAME}.access.log;
    error_log  /var/log/nginx/${NGINX_BASENAME}.error.log;

    ssl_certificate /etc/letsencrypt/live/$CERT_DOMAIN/fullchain.pem; # managed by Certbot
    ssl_certificate_key /etc/letsencrypt/live/$CERT_DOMAIN/privkey.pem; # managed by Certbot
    include /etc/letsencrypt/options-ssl-nginx.conf; # managed by Certbot
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem; # managed by Certbot

    root $FRONTEND_DEPLOY_DIR;
    index index.html;

    location / {
        try_files \$uri \$uri/ /index.html;
    }

    # Dedicated SSE location for HTTP/2 safety
    location /api/stream {
        proxy_pass http://127.0.0.1:$BACKEND_PORT/api/stream;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header Connection '';
        proxy_set_header Accept-Encoding '';
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 1d;
        proxy_send_timeout 1d;
        add_header X-Accel-Buffering no always;
        add_header Cache-Control no-cache always;
        gzip off;
        proxy_hide_header Content-Encoding;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:$BACKEND_PORT;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection '';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
        proxy_buffering off;
        proxy_read_timeout 3600s;
    }

    # WebSocket proxy for real-time events
    location /ws/ {
        proxy_pass http://127.0.0.1:$BACKEND_PORT;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 1d;
        proxy_send_timeout 1d;
    }

    # Static & media (if present)
    location /static/ {
        alias $FRONTEND_DEPLOY_DIR/staticfiles/;
        access_log off;
        expires 30d;
        add_header Cache-Control "public, max-age=2592000";
    }

    location /media/ {
        alias $FRONTEND_DEPLOY_DIR/media/;
        access_log off;
        expires 30d;
        add_header Cache-Control "public, max-age=2592000";
    }

    # PWA Icons
    location /icons/ {
        alias $FRONTEND_DEPLOY_DIR/icons/;
        access_log off;
        expires 7d;
        add_header Cache-Control "public, max-age=604800";

        # Handle CORS for PWA manifest
        add_header Access-Control-Allow-Origin "*";
        add_header Access-Control-Allow-Methods "GET, HEAD, OPTIONS";
        add_header Access-Control-Allow-Headers "Range";
    }

    # Manifest and Service Worker
    location ~ ^/(manifest\.json|sw\.js)$ {
        root $FRONTEND_DEPLOY_DIR;
        access_log off;
        expires 1d;
        add_header Cache-Control "public, max-age=86400";

        # Handle CORS
        add_header Access-Control-Allow-Origin "*";
        add_header Access-Control-Allow-Methods "GET, HEAD, OPTIONS";
    }
}
EOF

sudo ln -sf "$NGINX_CONF" "/etc/nginx/sites-enabled/${NGINX_BASENAME}.conf"
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl reload nginx

echo "=== Verification ==="
if netstat -tlnp 2>/dev/null | grep -q ":$BACKEND_PORT "; then
  echo "✅ Port $BACKEND_PORT is listening"
else
  echo "❌ Port $BACKEND_PORT is not listening"
fi

if curl -fsS "http://127.0.0.1:$BACKEND_PORT/api/status" >/dev/null 2>&1; then
  echo "✅ Backend health/status endpoint OK"
else
  echo "⚠️ Backend status check failed (expected /api/status)"
fi

echo ""
echo "=== Deployment Summary ==="
echo "Backend: systemd service $SERVICE_NAME on 127.0.0.1:$BACKEND_PORT"
echo "Frontend: deployed to $FRONTEND_DEPLOY_DIR"
echo "Nginx: site -> $NGINX_CONF (server_name: $SERVER_NAME)"
echo "Logs: journalctl -u $SERVICE_NAME -f, /var/log/${PROJECT_NAME}-gunicorn.log"
echo ""
echo "Tips: set SERVER_NAME env var and add DNS A record; configure TLS via certbot if desired."
