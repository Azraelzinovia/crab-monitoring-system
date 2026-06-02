"""
YOLOv8 Training Script — Crab Detection
Train custom YOLO model pada dataset kepiting
"""

import os
import shutil
import logging
import json
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── Config ─────────────────────────────────────────────────────────────────────
CONFIG = {
    "dataset_yaml"  : "datasets/yolo/crab_yolo.yaml",
    "base_model"    : "yolov8n.pt",           # nano untuk Pi 5
    "output_dir"    : "ai_models/yolo_runs",
    "output_name"   : "crab_detector",
    "weights_dir"   : "ai_models/weights",
    "epochs"        : 100,
    "imgsz"         : 640,
    "batch"         : 8,                      # turunkan ke 4 jika OOM di Pi
    "lr0"           : 0.01,
    "patience"      : 20,
    "device"        : "cpu",
    "workers"       : 2,
}


def check_dataset():
    """Validasi struktur dataset YOLO sebelum training."""
    yaml_path = Path(CONFIG["dataset_yaml"])
    if not yaml_path.exists():
        logger.error(f"Dataset YAML tidak ditemukan: {yaml_path}")
        logger.info("Buat file: datasets/yolo/crab_yolo.yaml")
        logger.info("Dan tambahkan gambar di: datasets/yolo/images/train/ dan val/")
        return False

    # Cek folder images
    for split in ["train", "val"]:
        img_dir   = Path("datasets/yolo/images") / split
        label_dir = Path("datasets/yolo/labels") / split
        if not img_dir.exists():
            logger.error(f"Folder tidak ditemukan: {img_dir}")
            return False
        imgs = list(img_dir.glob("*.jpg")) + list(img_dir.glob("*.png"))
        if len(imgs) == 0:
            logger.error(f"Tidak ada gambar di {img_dir}")
            return False
        logger.info(f"  {split}: {len(imgs)} gambar")

    return True


def train():
    """Jalankan training YOLOv8."""
    logger.info("🚀 Memulai Training YOLOv8 Crab Detector")
    logger.info(f"Config: {json.dumps(CONFIG, indent=2)}")

    if not check_dataset():
        logger.error("Dataset tidak valid. Training dibatalkan.")
        return

    try:
        from ultralytics import YOLO
    except ImportError:
        logger.error("ultralytics tidak terinstall. Jalankan: pip install ultralytics")
        return

    # Load base model
    model = YOLO(CONFIG["base_model"])
    logger.info(f"✅ Base model loaded: {CONFIG['base_model']}")

    # Training
    results = model.train(
        data    = CONFIG["dataset_yaml"],
        epochs  = CONFIG["epochs"],
        imgsz   = CONFIG["imgsz"],
        batch   = CONFIG["batch"],
        lr0     = CONFIG["lr0"],
        patience= CONFIG["patience"],
        device  = CONFIG["device"],
        workers = CONFIG["workers"],
        project = CONFIG["output_dir"],
        name    = CONFIG["output_name"],
        exist_ok= True,
        verbose = True,
        plots   = True,
        save    = True,
    )

    # Copy best weights ke folder ai_models/weights
    best_pt   = Path(CONFIG["output_dir"]) / CONFIG["output_name"] / "weights" / "best.pt"
    os.makedirs(CONFIG["weights_dir"], exist_ok=True)
    dest_pt   = Path(CONFIG["weights_dir"]) / "yolov8_crabs.pt"

    if best_pt.exists():
        shutil.copy(best_pt, dest_pt)
        logger.info(f"✅ Best model disalin ke: {dest_pt}")

        # Export ke ONNX
        logger.info("📦 Exporting ke ONNX...")
        export_model = YOLO(str(dest_pt))
        export_model.export(format="onnx", dynamic=True, simplify=True)
        dest_onnx = Path(CONFIG["weights_dir"]) / "yolov8_crabs.onnx"
        onnx_src  = dest_pt.with_suffix(".onnx")
        if onnx_src.exists():
            shutil.copy(onnx_src, dest_onnx)
            logger.info(f"✅ ONNX disimpan: {dest_onnx}")
    else:
        logger.error(f"Best weights tidak ditemukan di: {best_pt}")

    # Simpan metrics
    metrics = {
        "map50"     : float(results.results_dict.get("metrics/mAP50(B)", 0)),
        "map50_95"  : float(results.results_dict.get("metrics/mAP50-95(B)", 0)),
        "precision" : float(results.results_dict.get("metrics/precision(B)", 0)),
        "recall"    : float(results.results_dict.get("metrics/recall(B)", 0)),
    }
    metrics_path = Path(CONFIG["weights_dir"]) / "yolo_metrics.json"
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)

    logger.info("\n🎉 Training selesai!")
    logger.info(f"mAP50: {metrics['map50']:.3f} | mAP50-95: {metrics['map50_95']:.3f}")
    logger.info(f"Precision: {metrics['precision']:.3f} | Recall: {metrics['recall']:.3f}")


def validate():
    """Validasi model yang sudah ditraining."""
    model_path = Path(CONFIG["weights_dir"]) / "yolov8_crabs.pt"
    if not model_path.exists():
        logger.error(f"Model tidak ditemukan: {model_path}")
        return

    from ultralytics import YOLO
    model = YOLO(str(model_path))
    results = model.val(data=CONFIG["dataset_yaml"], device=CONFIG["device"])
    logger.info(f"Validation mAP50: {results.box.map50:.3f}")


def benchmark():
    """Benchmark kecepatan inference."""
    model_path = Path(CONFIG["weights_dir"]) / "yolov8_crabs.pt"
    if not model_path.exists():
        logger.error("Model belum ditraining")
        return

    from ultralytics import YOLO
    import numpy as np, time

    model = YOLO(str(model_path))
    dummy = np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8)
    times = []

    logger.info("Benchmarking 50 frames...")
    for _ in range(50):
        t = time.time()
        model(dummy, verbose=False)
        times.append((time.time() - t) * 1000)

    avg = sum(times) / len(times)
    logger.info(f"Avg: {avg:.1f}ms | FPS: {1000/avg:.1f}")


if __name__ == "__main__":
    import sys
    cmd = sys.argv[1] if len(sys.argv) > 1 else "train"
    if   cmd == "train"    : train()
    elif cmd == "validate" : validate()
    elif cmd == "benchmark": benchmark()
    else:
        print("Usage: python train_yolo.py [train|validate|benchmark]")
