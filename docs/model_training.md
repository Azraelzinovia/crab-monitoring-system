# Panduan Training Model — Crab Monitoring System

## Arsitektur Model

| Model | Arsitektur | Task | Input Size | Target Accuracy |
|-------|-----------|------|-----------|----------------|
| YOLO Detector | YOLOv8n | Object Detection | 640×640 | mAP50 > 0.85 |
| Species Classifier | EfficientNet-B0 | 4-class Classification | 224×224 | >90% |
| Gender Classifier | EfficientNet-B0 | Binary Classification | 224×224 | >88% |
| Health Classifier | EfficientNet-B0 | 4-class Classification | 224×224 | >85% |

## 1. Persiapan Dataset

### Struktur Folder

```
datasets/
├── species/               # Dataset Species (per-class folder)
│   ├── Kepiting Bakau/    # Min. 200 gambar (300+ rekomendasi)
│   ├── Kepiting Rajungan/
│   ├── Kepiting Lumpur/
│   └── Kepiting Batu/
│
├── gender/                # Dataset Gender
│   ├── Jantan/
│   └── Betina/
│
├── health/                # Dataset Health
│   ├── Sehat/
│   ├── Kurang Sehat/
│   ├── Sakit/
│   └── Mati/
│
├── yolo/                  # Dataset YOLO (YOLO format)
│   ├── images/
│   │   ├── train/
│   │   └── val/
│   ├── labels/
│   │   ├── train/
│   │   └── val/
│   └── crab_yolo.yaml
│
└── scraped/               # Auto-scraped data
    └── species_data.json
```

### Tips Pengumpulan Data
- **Variasi sudut pandang**: foto dari atas, samping, depan
- **Variasi pencahayaan**: siang, malam, buatan
- **Variasi latar belakang**: pasir, lumpur, air
- **Resolusi**: minimal 640×640 pixel
- **Format**: JPEG atau PNG

### Augmentasi yang Disarankan
- Horizontal/vertical flip
- Rotasi 0-360°
- Brightness/contrast variation
- Gaussian noise
- Cropping dan zooming

## 2. Training YOLO Detection

### Format Anotasi YOLO
```
# File: datasets/yolo/labels/train/image001.txt
# Format: class_id cx cy w h (semua relative [0-1])
0 0.5 0.45 0.6 0.7
```

### File Konfigurasi YAML
```yaml
# datasets/yolo/crab_yolo.yaml
path: datasets/yolo
train: images/train
val: images/val

nc: 4  # number of classes
names:
  0: Kepiting Bakau
  1: Kepiting Rajungan
  2: Kepiting Lumpur
  3: Kepiting Batu
```

### Command Training
```bash
cd crab-monitoring-system

# Activate virtual environment
source .venv/bin/activate

# Training
yolo train \
    data=datasets/yolo/crab_yolo.yaml \
    model=yolov8n.pt \
    epochs=100 \
    imgsz=640 \
    batch=8 \
    lr0=0.01 \
    device=cpu \
    project=ai_models/yolo_runs \
    name=crab_detector \
    patience=20

# Export ke ONNX
yolo export \
    model=ai_models/yolo_runs/crab_detector/weights/best.pt \
    format=onnx \
    dynamic=True \
    simplify=True

# Copy model
cp ai_models/yolo_runs/crab_detector/weights/best.pt ai_models/weights/yolov8_crabs.pt
cp ai_models/yolo_runs/crab_detector/weights/best.onnx ai_models/weights/yolov8_crabs.onnx
```

## 3. Training Species/Gender/Health Classifier

```bash
# Training species classifier
python ai_models/training/train_species.py

# Untuk gender classifier (sama strukturnya)
# Edit ai_models/training/train_species.py:
# - dataset_dir: "datasets/gender"
# - num_classes: 2
# - class_names: ["Jantan", "Betina"]
# - model_name: "gender_classifier.pt"

# Untuk health classifier:
# - dataset_dir: "datasets/health"
# - num_classes: 4
# - class_names: ["Sehat", "Kurang Sehat", "Sakit", "Mati"]
# - model_name: "health_classifier.pt"
```

## 4. Evaluasi Model

```bash
# Validasi YOLO
yolo val model=ai_models/weights/yolov8_crabs.pt data=datasets/yolo/crab_yolo.yaml

# Benchmark inference speed di Pi
python -c "
from ai_models.detection.yolo_detector import YOLOCrabDetector
detector = YOLOCrabDetector('ai_models/weights/yolov8_crabs.pt')
result = detector.benchmark(num_frames=50)
print(result)
"
```

## 5. Tips Optimasi Performa di Raspberry Pi 5

### Gunakan YOLOv8n (nano) bukan YOLOv8l
```bash
# Nano model: ~6MB, ~30 FPS di Pi 5
# Large model: ~87MB, ~5 FPS di Pi 5
yolo train model=yolov8n.pt ...  # Gunakan ini untuk Pi
```

### Ekspor ke ONNX dengan Quantization
```bash
# INT8 quantization (50% lebih cepat, akurasi sedikit turun)
yolo export model=best.pt format=onnx dynamic=True simplify=True half=True
```

### Kurangi Resolusi Input
```python
# Di .env
CAMERA_1_WIDTH=640
CAMERA_1_HEIGHT=480
YOLO_MODEL_PATH=ai_models/weights/yolov8_crabs.onnx  # Gunakan ONNX
```

### Frame Skipping
```python
# Proses 1 dari 2 frame untuk menghemat CPU
DETECTION_FRAME_SKIP=2  # Tambahkan ke config
```

## 6. Transfer Learning dari Model Pre-trained

Jika dataset terbatas (<100 gambar/kelas):

```bash
# Gunakan model yang sudah pre-trained pada dataset kepiting umum
# Opsi 1: Fine-tune dari YOLOv8 COCO (yang sudah mengenal animal)
# Opsi 2: Gunakan dataset dari Kaggle terlebih dahulu

python -c "
from ai_models.detection.yolo_detector import YOLOCrabDetector
# Model akan auto-download yolov8n.pt dari Ultralytics
detector = YOLOCrabDetector('yolov8n.pt')
"
```
