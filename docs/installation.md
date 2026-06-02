# Panduan Instalasi Lengkap — Crab Monitoring System

## Persyaratan Sistem

| Komponen | Minimum | Rekomendasi |
|----------|---------|-------------|
| Hardware | Raspberry Pi 5 4GB | Raspberry Pi 5 8GB |
| Storage | 64GB SSD | 256GB NVMe SSD |
| OS | Raspberry Pi OS 64-bit | Raspberry Pi OS 64-bit (Bookworm) |
| Python | 3.11+ | 3.11 |
| RAM | 4GB | 8GB |

## 1. Metode Cepat — Docker (Rekomendasi PC/Server)

```bash
# Clone proyek
git clone https://github.com/your-repo/crab-monitoring-system.git
cd crab-monitoring-system

# Copy environment
cp .env.example .env

# Jalankan semua service
docker-compose -f docker/docker-compose.yml up -d

# Cek status
docker-compose -f docker/docker-compose.yml ps
```

Akses:
- **Dashboard**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs

## 2. Raspberry Pi 5 — Instalasi Otomatis

```bash
# Transfer proyek ke Pi
scp -r crab-monitoring-system/ pi@raspberrypi.local:~/

# SSH ke Pi
ssh pi@raspberrypi.local

# Jalankan setup script
cd ~/crab-monitoring-system
chmod +x deployment/setup_raspberry_pi.sh
bash deployment/setup_raspberry_pi.sh
```

## 3. Instalasi Manual (Step-by-step)

### 3.1 PostgreSQL

```bash
sudo apt-get install postgresql postgresql-contrib -y
sudo systemctl start postgresql
sudo -u postgres createuser crab_admin -P
sudo -u postgres createdb crab_monitoring -O crab_admin
sudo -u postgres psql -d crab_monitoring < database/schema.sql
```

### 3.2 Python Backend

```bash
cd crab-monitoring-system
python3.11 -m venv .venv
source .venv/bin/activate

pip install -r backend/requirements.txt
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 3.3 React Frontend

```bash
cd frontend
npm install
npm start          # Development
# atau
npm run build      # Production build
```

## 4. Koneksi Kamera

### USB Camera
```bash
# Cek kamera yang tersambung
v4l2-ctl --list-devices

# Test kamera 1
v4l2-ctl -d /dev/video0 --list-formats-ext

# Set di .env
CAMERA_1_INDEX=0
CAMERA_2_INDEX=1
```

### Pi Camera v3
```bash
# Enable di raspi-config
sudo raspi-config -> Interface Options -> Camera

# Test
rpicam-still -o test.jpg

# Set di .env (gunakan libcamera backend)
CAMERA_1_INDEX=0  # Akan dideteksi otomatis via picamera2
```

## 5. Training Model YOLO

```bash
# Siapkan dataset
datasets/
└── species/
    ├── Kepiting Bakau/    (min. 100 gambar)
    ├── Kepiting Rajungan/ (min. 100 gambar)
    ├── Kepiting Lumpur/   (min. 100 gambar)
    └── Kepiting Batu/     (min. 100 gambar)

# Jalankan training
python ai_models/training/train_species.py

# Training YOLO detection
yolo train data=datasets/crab_yolo.yaml model=yolov8n.pt epochs=100 imgsz=640 batch=8
```

## 6. Web Scraping

```bash
# Jalankan scraper manual
python scraping/crab_scraper.py

# Data tersimpan di datasets/scraped/species_data.json
# Dan otomatis di-sync ke database
```

## 7. Optimasi Performa di Raspberry Pi 5

```bash
# 1. Tingkatkan GPU memory
echo "gpu_mem=256" | sudo tee -a /boot/config.txt

# 2. Set CPU governor ke performance
echo "performance" | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor

# 3. Enable hardware video acceleration
sudo apt-get install libgstreamer1.0-dev -y

# 4. Gunakan ONNX runtime (lebih cepat dari PyTorch)
# Model otomatis di-export ke ONNX saat training selesai

# 5. Kurangi resolusi kamera untuk FPS lebih tinggi
CAMERA_1_WIDTH=640
CAMERA_1_HEIGHT=480
CAMERA_FPS=30
STREAM_FPS=20
```

## 8. Monitoring Service

```bash
# Status service
sudo systemctl status crab-monitor

# Lihat logs real-time
sudo journalctl -u crab-monitor -f

# Restart jika error
sudo systemctl restart crab-monitor

# Stop service
sudo systemctl stop crab-monitor
```

## 9. Backup Database

```bash
# Backup
pg_dump -U crab_admin crab_monitoring > backup_$(date +%Y%m%d).sql

# Restore
psql -U crab_admin crab_monitoring < backup_20240101.sql
```

## Troubleshooting

| Masalah | Solusi |
|---------|--------|
| Kamera tidak terdeteksi | Cek `v4l2-ctl --list-devices`, pastikan user di grup `video` |
| Model YOLO tidak load | Download `yolov8n.pt` dari ultralytics, atau gunakan demo mode |
| Database tidak connect | Cek `sudo systemctl status postgresql` |
| FPS rendah | Kurangi resolusi kamera, gunakan ONNX model |
| Port 8000 sudah dipakai | Ubah `API_PORT` di `.env` |

## Target Performa

| Metric | Target | Catatan |
|--------|--------|---------|
| Detection FPS | 15-30 FPS | Dengan model YOLOv8n ONNX |
| Accuracy Spesies | >90% | Setelah training dengan 500+ gambar/kelas |
| Accuracy Kesehatan | >85% | Bergantung kualitas dataset |
| Latency API | <50ms | Lokal, tanpa network overhead |
| DB Response | <10ms | Index dioptimasi |
