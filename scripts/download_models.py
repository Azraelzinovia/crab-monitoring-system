"""
Download Models Script
Download YOLOv8 base model dan model pre-trained jika tersedia
Jalankan: python scripts/download_models.py
"""

import os
import sys
import urllib.request
import hashlib
from pathlib import Path

WEIGHTS_DIR = Path("ai_models/weights")

MODELS = [
    {
        "name": "YOLOv8n (base model)",
        "filename": "yolov8n.pt",
        "url": "https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt",
        "size_mb": 6.2,
    },
    {
        "name": "YOLOv8s (small — lebih akurat)",
        "filename": "yolov8s.pt",
        "url": "https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8s.pt",
        "size_mb": 22.4,
        "optional": True,
    },
]


def download_file(url: str, dest: Path, name: str) -> bool:
    """Download file dengan progress bar."""
    print(f"\n📥 Downloading: {name}")
    print(f"   URL: {url}")
    print(f"   Dest: {dest}")

    def progress(count, block_size, total_size):
        if total_size > 0:
            pct = count * block_size / total_size * 100
            pct = min(pct, 100)
            bar = "█" * int(pct // 5) + "░" * (20 - int(pct // 5))
            print(f"\r   [{bar}] {pct:.0f}%", end="", flush=True)

    try:
        urllib.request.urlretrieve(url, dest, reporthook=progress)
        print(f"\n   ✅ Selesai: {dest.stat().st_size / 1024 / 1024:.1f}MB")
        return True
    except Exception as e:
        print(f"\n   ❌ Gagal: {e}")
        return False


def main():
    print("🤖 Download AI Models untuk Crab Monitoring System")
    print("=" * 55)

    WEIGHTS_DIR.mkdir(parents=True, exist_ok=True)

    # Check ultralytics
    try:
        from ultralytics import YOLO
        print("✅ ultralytics tersedia")
        use_ultralytics = True
    except ImportError:
        print("⚠️  ultralytics tidak terinstall — download manual")
        use_ultralytics = False

    downloaded = 0
    for model in MODELS:
        dest = WEIGHTS_DIR / model["filename"]

        if dest.exists():
            size_mb = dest.stat().st_size / 1024 / 1024
            print(f"\n⏭️  {model['name']} sudah ada ({size_mb:.1f}MB) — skip")
            continue

        if model.get("optional"):
            print(f"\n⏭️  {model['name']} (optional) — skip")
            continue

        if use_ultralytics:
            try:
                print(f"\n📥 Downloading via ultralytics: {model['filename']}")
                from ultralytics import YOLO
                YOLO(model["filename"])  # auto-download ke cache
                import shutil, torch
                cache_path = Path(torch.hub.get_dir()) / "ultralytics" / "assets" / model["filename"]
                if cache_path.exists():
                    shutil.copy(cache_path, dest)
                    print(f"   ✅ Disalin ke: {dest}")
                    downloaded += 1
                    continue
            except Exception:
                pass

        # Fallback: download langsung
        if download_file(model["url"], dest, model["name"]):
            downloaded += 1

    print(f"\n✅ Selesai! {downloaded} model didownload ke {WEIGHTS_DIR}")
    print("\nCatatan:")
    print("  - Model ini adalah base model (pre-trained pada COCO dataset)")
    print("  - Untuk deteksi kepiting, perlu fine-tuning dengan dataset Anda")
    print("  - Jalankan: python ai_models/training/train_yolo.py")


if __name__ == "__main__":
    main()
