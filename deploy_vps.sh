#!/bin/bash
# ==============================================================================
# Script de déploiement automatique RecrutIA RH sur VPS Hostinger (Ubuntu/Debian)
# ==============================================================================

set -e

echo "========================================================"
echo "🚀 [1/5] Mise à jour du système et installation des outils..."
echo "========================================================"
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3-pip python3-venv git nginx

echo "========================================================"
echo "📥 [2/5] Récupération du projet depuis GitHub..."
echo "========================================================"
sudo rm -rf /var/www/recrutia-rh
sudo mkdir -p /var/www
cd /var/www
sudo git clone https://github.com/Fatima-ezahrae22/recrutia-rh.git
cd /var/www/recrutia-rh

echo "========================================================"
echo "⚙️ [3/5] Configuration de l'environnement Python..."
echo "========================================================"
sudo python3 -m venv venv
sudo /var/www/recrutia-rh/venv/bin/pip install --upgrade pip
sudo /var/www/recrutia-rh/venv/bin/pip install -r requirements.txt
sudo /var/www/recrutia-rh/venv/bin/python3 -m spacy download fr_core_news_sm || true

echo "========================================================"
echo "🔄 [4/5] Configuration du service automatique (Systemd)..."
echo "========================================================"
sudo tee /etc/systemd/system/recrutia.service > /dev/null <<EOF
[Unit]
Description=Service FastAPI RecrutIA RH
After=network.target

[Service]
User=root
WorkingDirectory=/var/www/recrutia-rh
ExecStart=/var/www/recrutia-rh/venv/bin/uvicorn backend.main:app --host 127.0.0.1 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable recrutia
sudo systemctl restart recrutia

echo "========================================================"
echo "🌐 [5/5] Configuration du serveur Web Nginx..."
echo "========================================================"
sudo tee /etc/nginx/sites-available/recrutia > /dev/null <<EOF
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name _;

    client_max_body_size 50M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location /ws/ {
        proxy_pass http://127.0.0.1:8000/ws/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "Upgrade";
    }
}
EOF

sudo rm -f /etc/nginx/sites-enabled/default
sudo ln -sf /etc/nginx/sites-available/recrutia /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

echo ""
echo "========================================================"
echo "🎉 FÉLICITATIONS ! DÉPLOIEMENT TERMINÉ AVEC SUCCÈS !"
echo "========================================================"
echo "Accédez directement à votre site sur :"
echo "👉 Espace Candidat : http://$(curl -s ifconfig.me)/candidat"
echo "👉 Espace RH       : http://$(curl -s ifconfig.me)/rh"
echo "========================================================"
