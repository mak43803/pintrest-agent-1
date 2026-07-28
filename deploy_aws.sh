#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════
# Baddies Beauty Pinterest AI Agent — AWS Ubuntu Deployment Script
# Run this ONCE on your fresh AWS Ubuntu server after SSHing in.
# ═══════════════════════════════════════════════════════════════════════════
set -e

echo "======================================================"
echo " STEP 1: System Update & Base Dependencies"
echo "======================================================"
sudo apt update -y
sudo apt install -y \
    python3.12 python3.12-venv python3.12-dev python3-pip \
    git curl wget unzip \
    xvfb x11vnc \
    fonts-liberation fonts-noto-color-emoji \
    libxss1 libappindicator1 libindicator7 \
    libasound2 libnspr4 libnss3 libxcb-dri3-0 \
    libgbm1 libxshmfence1 \
    ca-certificates gnupg lsb-release

echo ""
echo "======================================================"
echo " STEP 2: Install Google Chrome (Required for Agent)"
echo "======================================================"
wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" | \
    sudo tee /etc/apt/sources.list.d/google-chrome.list
sudo apt update -y
sudo apt install -y google-chrome-stable

echo "Chrome version: $(google-chrome --version)"

echo ""
echo "======================================================"
echo " STEP 3: Install Ollama (Local AI — qwen3:8b)"
echo "======================================================"
curl -fsSL https://ollama.com/install.sh | sh
sleep 3
ollama pull qwen3:8b
echo "Ollama + qwen3:8b installed."

echo ""
echo "======================================================"
echo " STEP 4: Clone Repository from GitHub"
echo "======================================================"
cd ~
if [ -d "pintrest-agent-1" ]; then
    echo "Repo already exists. Pulling latest..."
    cd pintrest-agent-1
    git pull origin main
else
    git clone https://github.com/mak43803/pintrest-agent-1.git
    cd pintrest-agent-1
fi

echo ""
echo "======================================================"
echo " STEP 5: Python Virtual Environment & Dependencies"
echo "======================================================"
python3.12 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "======================================================"
echo " STEP 6: Install Playwright Chromium Drivers"
echo "======================================================"
playwright install chromium
playwright install-deps chromium

echo ""
echo "======================================================"
echo " STEP 7: Create .env File"
echo "======================================================"
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo ""
    echo ">>> .env file created. Fill in your credentials:"
    echo "    nano .env"
    echo ""
fi

echo ""
echo "======================================================"
echo " STEP 8: Create Required Directories"
echo "======================================================"
mkdir -p images logs database browser_session config fonts

echo ""
echo "======================================================"
echo " STEP 9: Setup Xvfb Virtual Display Service"
echo "======================================================"
sudo tee /etc/systemd/system/xvfb.service > /dev/null <<EOF
[Unit]
Description=X Virtual Framebuffer
After=network.target

[Service]
ExecStart=/usr/bin/Xvfb :99 -screen 0 1280x900x24 -ac +extension GLX +render -noreset
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable xvfb
sudo systemctl start xvfb
echo "Xvfb (virtual display :99) started."

echo ""
echo "======================================================"
echo " STEP 10: Create Agent Systemd Service (Auto-Restart)"
echo "======================================================"
REPO_PATH=$(pwd)
sudo tee /etc/systemd/system/pinterest-agent.service > /dev/null <<EOF
[Unit]
Description=Baddies Beauty Pinterest AI Agent
After=network.target xvfb.service
Requires=xvfb.service

[Service]
Type=simple
User=ubuntu
WorkingDirectory=${REPO_PATH}
Environment="DISPLAY=:99"
Environment="PATH=${REPO_PATH}/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
ExecStart=${REPO_PATH}/venv/bin/python main.py
Restart=always
RestartSec=10
StandardOutput=append:${REPO_PATH}/logs/agent.log
StandardError=append:${REPO_PATH}/logs/agent.log

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable pinterest-agent

echo ""
echo "DONE! See instructions below."
