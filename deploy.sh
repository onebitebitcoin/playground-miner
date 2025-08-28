#!/usr/bin/env bash

set -euo pipefail

# Playground Miner deployment script (Ubuntu)
# Based on ../training/deploy.sh, adapted for this repo layout.
#
# Usage:
#   SERVER_NAME=playground.onebitebitcoin.com BACKEND_PORT=8002 sudo -E ./deploy.sh
#
# Notes:
# - Expects Ubuntu with apt. Installs Node LTS, Python, Nginx.
# - Backend (Django) runs via systemd + gunicorn on 127.0.0.1:$BACKEND_PORT.
# - Frontend (Vite) is built and served by Nginx from /var/www/$PROJECT_NAME.

PROJECT_NAME="playground"
ROOT_DIR=$(pwd)
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"
FRONTEND_DEPLOY_DIR="/var/www/${PROJECT_NAME}"
SERVICE_NAME="${PROJECT_NAME}-backend"
BACKEND_PORT="${BACKEND_PORT:-8002}"
# Default to the intended domain; override via SERVER_NAME env
SERVER_NAME="${SERVER_NAME:-playground.onebitebitcoin.com}"

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

  echo "Running migrations..."
  python manage.py migrate --noinput

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
  sudo cp -r dist/* "$FRONTEND_DEPLOY_DIR"/
  sudo chown -R www-data:www-data "$FRONTEND_DEPLOY_DIR"/
  sudo chmod -R 755 "$FRONTEND_DEPLOY_DIR"/
else
  echo "package.json not found in $FRONTEND_DIR; skipping frontend build"
fi

echo "=== systemd: Backend service ==="
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
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
ExecStart=$BACKEND_DIR/venv/bin/gunicorn --workers 3 --bind 127.0.0.1:$BACKEND_PORT playground_server.wsgi:application
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
echo "Restarting backend service..."
sudo systemctl restart "$SERVICE_NAME" || true

sleep 3
if sudo systemctl is-active --quiet "$SERVICE_NAME"; then
  echo "✅ Backend service is active"
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
# Name the nginx config after the server_name (e.g., playground.onebitebitcoin.com.conf)
NGINX_BASENAME="${SERVER_NAME:-$PROJECT_NAME}"
NGINX_CONF="/etc/nginx/sites-available/${NGINX_BASENAME}"
sudo bash -c "cat > '$NGINX_CONF'" <<EOF
server {
    listen 80;
    server_name $SERVER_NAME;

    root $FRONTEND_DEPLOY_DIR;
    index index.html;

    location /api/ {
        proxy_pass http://127.0.0.1:$BACKEND_PORT;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
    }

    location / {
        try_files \$uri \$uri/ /index.html;
    }
}
EOF

sudo ln -sf "$NGINX_CONF" "/etc/nginx/sites-enabled/${NGINX_BASENAME}"
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
