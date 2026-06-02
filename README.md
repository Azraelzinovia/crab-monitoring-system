# 🦀 Crab Monitoring System

Sistem monitoring kepiting otomatis berbasis Raspberry Pi 5 dengan Computer Vision, Deep Learning, dan Web Dashboard real-time.

## 🌟 Fitur Utama

- **Deteksi Real-time** menggunakan YOLOv8 dengan dual kamera
- **Klasifikasi Otomatis**: Jenis, jenis kelamin, kesehatan
- **Estimasi Ukuran & Berat** via Computer Vision Measurement
- **Web Dashboard** dengan live streaming & statistik
- **Database PostgreSQL** untuk pencatatan lengkap
- **Web Scraping** otomatis dari sumber ilmiah
- **REST API** dengan dokumentasi Swagger
- **Docker Deployment** siap pakai

## 🏗️ Arsitektur

```
Kamera 1 (Atas) ──┐
                   ├─→ Raspberry Pi 5 ─→ AI Pipeline ─→ PostgreSQL ─→ FastAPI ─→ React Dashboard
Kamera 2 (Samping)─┘
```

## 🚀 Quick Start

```bash
# Clone dan masuk ke direktori
cd crab-monitoring-system

# Copy environment file
cp .env.example .env

# Jalankan dengan Docker Compose
docker-compose up -d

# Akses Dashboard
open http://localhost:3000

# Akses API Docs
open http://localhost:8000/docs
```

## 📁 Struktur Proyek

```
crab-monitoring-system/
├── backend/          # FastAPI Backend + AI Pipeline
├── frontend/         # React Dashboard
├── ai_models/        # YOLOv8, CNN Models, Training Scripts
├── scraping/         # Web Scraper Modules
├── database/         # SQL Migrations & ERD
├── datasets/         # Dataset Management
├── docker/           # Docker Configurations
├── docs/             # Documentation
└── deployment/       # Raspberry Pi Setup
```

## 📋 Persyaratan Hardware

- Raspberry Pi 5 (8GB RAM recommended)
- Camera Module 1 (Tampak Atas) — Pi Camera v3 atau USB
- Camera Module 2 (Tampak Samping) — Pi Camera v3 atau USB
- SSD Storage (min 64GB)
- Koneksi Internet

## 🛠️ Persyaratan Software

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- PostgreSQL 15+

## 📖 Dokumentasi

Lihat folder `docs/` untuk panduan lengkap:
- [Panduan Instalasi](docs/installation.md)
- [Panduan Training Model](docs/model_training.md)
- [Panduan Deployment Pi](docs/raspberry_pi_setup.md)
- [API Reference](docs/api_reference.md)

## 📊 Performance Target

- Detection Speed: 15–30 FPS pada Raspberry Pi 5
- Accuracy Species: >90%
- Accuracy Health: >85%
- Accuracy Gender: >88%

## 📄 Lisensi

MIT License — Bebas digunakan untuk riset dan industri.
