#!/bin/bash
# =============================================================
# Raspberry Pi 5 — Setup Script untuk Crab Monitoring System
# Jalankan sebagai: bash setup_raspberry_pi.sh
# =============================================================

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname $SCRIPT_DIR)"

echo "============================================="
echo " 🦀 Crab Monitoring System - Pi 5 Setup    "
echo "============================================="
echo ""

# ── Step 1: Update sistem ─────────────────────────────────────────────────────
echo "📦 Step 1: Updating system packages..."
sudo apt-get update && sudo apt-get upgrade -y
sudo apt-get install -y \
    python3.11 python3.11-dev python3.11-venv \
    python3-pip \
    libopencv-dev \
    python3-opencv \
    libatlas-base-dev \
    libhdf5-dev \
    libhdf5-serial-dev \
    libffi-dev \
    libssl-dev \
    v4l-utils \
    git curl wget \
    postgresql postgresql-contrib \
    nginx \
    libglib2.0-dev \
    libjpeg-dev \
    libtiff-dev \
    libpng-dev \
    libcamera-dev

echo "✅ System packages installed"

# ── Step 2: Configure Cameras ─────────────────────────────────────────────────
echo ""
echo "📷 Step 2: Configuring cameras..."

# Enable camera interface
sudo raspi-config nonint do_camera 0

# Add user to video group for USB cameras
sudo usermod -aG video $USER

# Create udev rules for persistent camera device naming
sudo tee /etc/udev/rules.d/99-crab-cameras.rules << 'EOF'
# Camera 1 (Top View) — adjust idVendor/idProduct for your camera
SUBSYSTEM=="video4linux", ATTR{index}=="0", SYMLINK+="crab_cam_top"
# Camera 2 (Side View) — adjust idVendor/idProduct for your camera
SUBSYSTEM=="video4linux", ATTR{index}=="1", SYMLINK+="crab_cam_side"
EOF

sudo udevadm control --reload-rules
echo "✅ Camera configuration done"

# ── Step 3: Python Virtual Environment ────────────────────────────────────────
echo ""
echo "🐍 Step 3: Setting up Python virtual environment..."

cd "$PROJECT_DIR"
python3.11 -m venv .venv
source .venv/bin/activate

pip install --upgrade pip wheel setuptools

# Install PyTorch for ARM64 (Pi 5)
echo "Installing PyTorch for ARM64..."
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu

# Install project requirements
pip install -r backend/requirements.txt

echo "✅ Python environment ready"

# ── Step 4: PostgreSQL Setup ──────────────────────────────────────────────────
echo ""
echo "🗄️ Step 4: Setting up PostgreSQL..."

sudo systemctl enable postgresql
sudo systemctl start postgresql

sudo -u postgres psql << 'EOF'
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_user WHERE usename = 'crab_admin') THEN
        CREATE USER crab_admin WITH PASSWORD 'crab_secure_2024';
    END IF;
END
$$;
CREATE DATABASE IF NOT EXISTS crab_monitoring OWNER crab_admin;
GRANT ALL PRIVILEGES ON DATABASE crab_monitoring TO crab_admin;
EOF

# Apply schema
sudo -u postgres psql -d crab_monitoring < "$PROJECT_DIR/database/schema.sql"
echo "✅ PostgreSQL configured"

# ── Step 5: Environment File ──────────────────────────────────────────────────
echo ""
echo "⚙️ Step 5: Creating environment file..."

RASPBERRY_IP=$(hostname -I | awk '{print $1}')
cat > "$PROJECT_DIR/backend/.env" << EOF
# Auto-generated on Raspberry Pi 5
API_HOST=0.0.0.0
API_PORT=8000
API_DEBUG=false

DATABASE_URL=postgresql+asyncpg://crab_admin:crab_secure_2024@localhost:5432/crab_monitoring

CAMERA_1_INDEX=0
CAMERA_2_INDEX=1
CAMERA_1_WIDTH=1280
CAMERA_1_HEIGHT=720
CAMERA_2_WIDTH=1280
CAMERA_2_HEIGHT=720
CAMERA_FPS=30

YOLO_MODEL_PATH=ai_models/weights/yolov8_crabs.pt
STREAM_FPS=15
LOG_LEVEL=INFO
LOG_FILE=logs/crab_monitor.log
IMAGE_STORAGE_PATH=storage/images
EOF

echo "✅ Environment file created"

# ── Step 6: Systemd Service ───────────────────────────────────────────────────
echo ""
echo "🔧 Step 6: Creating systemd autostart service..."

sudo tee /etc/systemd/system/crab-monitor.service << EOF
[Unit]
Description=Crab Monitoring System
After=network.target postgresql.service
Requires=postgresql.service

[Service]
Type=simple
User=$USER
WorkingDirectory=$PROJECT_DIR/backend
Environment=PATH=$PROJECT_DIR/.venv/bin:/usr/local/bin:/usr/bin:/bin
ExecStart=$PROJECT_DIR/.venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000 --workers 1
Restart=always
RestartSec=5
StandardOutput=append:$PROJECT_DIR/logs/backend.log
StandardError=append:$PROJECT_DIR/logs/backend.log

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable crab-monitor
echo "✅ Systemd service created"

# ── Step 7: Nginx Configuration ───────────────────────────────────────────────
echo ""
echo "🌐 Step 7: Configuring Nginx..."

sudo cp "$PROJECT_DIR/docker/nginx.conf" /etc/nginx/nginx.conf
sudo systemctl enable nginx
sudo nginx -t && sudo systemctl restart nginx
echo "✅ Nginx configured"

# ── Step 8: Download Base YOLO Model ─────────────────────────────────────────
echo ""
echo "🤖 Step 8: Downloading YOLOv8 base model..."

mkdir -p "$PROJECT_DIR/ai_models/weights"
cd "$PROJECT_DIR/ai_models/weights"

if [ ! -f "yolov8n.pt" ]; then
    wget -q https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt
    echo "✅ YOLOv8n downloaded (base model — train on crab dataset for best results)"
fi

cd "$PROJECT_DIR"

# ── Step 9: Start Services ────────────────────────────────────────────────────
echo ""
echo "🚀 Step 9: Starting services..."
sudo systemctl start crab-monitor

sleep 3
if systemctl is-active --quiet crab-monitor; then
    echo "✅ Crab Monitor service is running!"
else
    echo "⚠️ Service might need a moment to start. Check: sudo journalctl -u crab-monitor -f"
fi

# ── Done ──────────────────────────────────────────────────────────────────────
echo ""
echo "============================================="
echo " ✅ Installation Complete!                  "
echo "============================================="
echo ""
echo "📊 Dashboard: http://$RASPBERRY_IP:3000"
echo "🔧 API:       http://$RASPBERRY_IP:8000"
echo "📖 API Docs:  http://$RASPBERRY_IP:8000/docs"
echo ""
echo "Commands:"
echo "  Start:   sudo systemctl start crab-monitor"
echo "  Stop:    sudo systemctl stop crab-monitor"
echo "  Logs:    sudo journalctl -u crab-monitor -f"
echo "  Status:  sudo systemctl status crab-monitor"
echo ""
echo "⚠️  Next steps:"
echo "  1. Train YOLO model: python ai_models/training/train_yolo.py"
echo "  2. Run scraper:      python scraping/crab_scraper.py"
echo "  3. Build frontend:   cd frontend && npm install && npm run build"
echo ""
