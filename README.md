# 🦀 SmartCrab Monitoring System

<div align="center">

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109-green?logo=fastapi)
![React](https://img.shields.io/badge/React-18-blue?logo=react)
![YOLOv8](https://img.shields.io/badge/YOLOv8-Ultralytics-orange)
![Raspberry Pi](https://img.shields.io/badge/Raspberry%20Pi-5-red?logo=raspberrypi)
![License](https://img.shields.io/badge/License-MIT-green)
[![CI/CD](https://github.com/Azraelzinovia/crab-monitoring-system/actions/workflows/ci.yml/badge.svg)](https://github.com/Azraelzinovia/crab-monitoring-system/actions)

**Sistem deteksi, klasifikasi, dan monitoring kepiting otomatis berbasis AI pada Raspberry Pi 5**

[📖 Dokumentasi](#dokumentasi) · [🚀 Quick Start](#quick-start) · [🔧 API Docs](http://localhost:8000/docs) · [🎯 Features](#fitur)

</div>

---

## 🎯 Fitur

| Fitur | Teknologi | Detail |
|-------|-----------|--------|
| **Deteksi Real-time** | YOLOv8 + ByteTrack | 15–30 FPS pada Raspberry Pi 5 |
| **Klasifikasi Spesies** | EfficientNet-B0 | 4 spesies (Bakau, Rajungan, Lumpur, Batu) |
| **Analisis Gender** | CNN | Jantan / Betina |
| **Status Kesehatan** | CNN + HSV Analysis | Sehat / Kurang Sehat / Sakit / Mati |
| **Pengukuran Fisik** | Camera Calibration | Panjang, Lebar, Estimasi Berat |
| **Dual Camera** | OpenCV | Tampak Atas + Tampak Samping |
| **Live Streaming** | MJPEG + WebSocket | Dashboard real-time |
| **Database** | PostgreSQL + SQLAlchemy | Async, indexed, dengan views |
| **Web Scraping** | BeautifulSoup + aiohttp | Wikipedia, GBIF, FAO, WoRMS |
| **Dashboard** | React 18 + Recharts | 5 halaman monitoring |

---

## 🏗️ Arsitektur

```
Kamera 1 (Atas) ─┐
                  ├─▶ AI Pipeline ─▶ PostgreSQL ─▶ FastAPI ─▶ React Dashboard
Kamera 2 (Samping)┘   │
                       ├── YOLOv8 Detection
                       ├── Species CNN
                       ├── Gender CNN
                       ├── Health CNN
                       └── Size Estimator
```

---

## 🚀 Quick Start

### Opsi 1 — Docker (Rekomendasi PC/Server)

```bash
git clone https://github.com/Azraelzinovia/crab-monitoring-system.git
cd crab-monitoring-system
cp .env.example .env
docker compose -f docker/docker-compose.yml up -d
```

Akses: **http://localhost:3000**

### Opsi 2 — Raspberry Pi 5 (Auto-setup)

```bash
git clone https://github.com/Azraelzinovia/crab-monitoring-system.git
cd crab-monitoring-system
bash deployment/setup_raspberry_pi.sh
```

### Opsi 3 — Windows (Development)

```powershell
# Frontend saja (demo mode)
cd frontend
npm install
$env:REACT_APP_API_URL="http://localhost:8000"
$env:DANGEROUSLY_DISABLE_HOST_CHECK="true"
npm start

# Atau gunakan script PowerShell
.\run_windows.ps1 -Method Frontend
```

---

## 📁 Struktur Proyek

```
crab-monitoring-system/
├── backend/              # FastAPI + SQLAlchemy async
│   ├── core/             # Config, Database
│   ├── api/routes/       # 6 router modules
│   ├── models/           # ORM + Pydantic schemas
│   └── services/         # Camera + Detection orchestrator
├── ai_models/            # AI Pipeline
│   ├── detection/        # YOLOv8 wrapper
│   ├── classification/   # Species, Gender, Health CNN
│   ├── measurement/      # Size estimation
│   ├── analysis/         # Body part detector
│   └── training/         # Training scripts (YOLO + CNN)
├── frontend/             # React 18 Dashboard
│   └── src/pages/        # Dashboard, Deteksi, Spesies, Kesehatan, Settings
├── database/             # PostgreSQL schema + seed data
├── scraping/             # Multi-source web scrapers
├── docker/               # Dockerfiles + Nginx + Compose
├── deployment/           # Raspberry Pi setup script
├── docs/                 # Panduan lengkap
└── scripts/              # DB init, model download
```

---

## 📊 Target Performa

| Metric | Target | Keterangan |
|--------|--------|------------|
| Detection FPS | **15–30 FPS** | YOLOv8n ONNX, resolusi 640×480 |
| Species Accuracy | **>90%** | Setelah training 500+ gambar/kelas |
| Gender Accuracy | **>88%** | Dataset balanced |
| Health Accuracy | **>85%** | CNN + HSV color analysis |
| API Latency | **<50ms** | Lokal, PostgreSQL indexed |

---

## 🤖 Training Model

```bash
# Download base model
python scripts/download_models.py

# Training species classifier
python ai_models/training/train_species.py

# Training YOLO detector
python ai_models/training/train_yolo.py

# Training gender classifier (edit config di file)
python ai_models/training/train_species.py --task gender

# Benchmark kecepatan di Pi
python ai_models/training/train_yolo.py benchmark
```

---

## 📖 Dokumentasi

- [📦 Panduan Instalasi](docs/installation.md)
- [🤖 Panduan Training Model](docs/model_training.md)
- [🔧 API Reference](http://localhost:8000/docs) *(saat backend berjalan)*
- [🍓 Setup Raspberry Pi](deployment/setup_raspberry_pi.sh)

---

## 🌿 Species yang Didukung

| Spesies | Nama Ilmiah | Berat | Panjang |
|---------|-------------|-------|---------|
| Kepiting Bakau | *Scylla serrata* | 100–1200g | 8–20cm |
| Kepiting Rajungan | *Portunus pelagicus* | 50–400g | 6–18cm |
| Kepiting Lumpur | *Scylla olivacea* | 80–600g | 6–15cm |
| Kepiting Batu | *Charybdis feriata* | 100–800g | 7–17cm |

---

## 📜 License

MIT License — bebas digunakan untuk penelitian dan pengembangan.

---

<div align="center">
Made with ❤️ for Indonesian Aquaculture 🦀🇮🇩
</div>
