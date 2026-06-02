"""
Training Script — Species Classifier
Fine-tune EfficientNet-B0 pada dataset kepiting Indonesia
"""

try:
    import torch                                    # type: ignore[import]
    import torch.nn as nn                           # type: ignore[import]
    import torch.optim as optim                     # type: ignore[import]
    from torch.utils.data import DataLoader, Dataset  # type: ignore[import]
    from torchvision import transforms, models      # type: ignore[import]
    TORCH_AVAILABLE = True
except ImportError:
    torch = None        # type: ignore[assignment]
    nn = None           # type: ignore[assignment]
    optim = None        # type: ignore[assignment]
    DataLoader = None   # type: ignore[assignment]
    Dataset = None      # type: ignore[assignment]
    transforms = None   # type: ignore[assignment]
    models = None       # type: ignore[assignment]
    TORCH_AVAILABLE = False

try:
    import cv2          # type: ignore[import]
    CV2_AVAILABLE = True
except ImportError:
    cv2 = None          # type: ignore[assignment]
    CV2_AVAILABLE = False

from pathlib import Path
import numpy as np
import json
import logging
import time
from typing import Optional
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── Config ────────────────────────────────────────────────────────────────────
CONFIG = {
    "dataset_dir": "datasets/species",
    "output_dir": "ai_models/weights",
    "model_name": "species_classifier.pt",
    "num_classes": 4,
    "class_names": ["Kepiting Bakau", "Kepiting Rajungan", "Kepiting Lumpur", "Kepiting Batu"],
    "img_size": 224,
    "batch_size": 16,
    "epochs": 50,
    "learning_rate": 1e-4,
    "weight_decay": 1e-5,
    "patience": 10,         # Early stopping patience
    "train_split": 0.8,
    "val_split": 0.2,
    "device": "cuda" if torch.cuda.is_available() else "cpu",
    "num_workers": 2,
    "augmentation": True,
}


# ── Dataset ───────────────────────────────────────────────────────────────────

class CrabDataset(Dataset):
    """
    Dataset kepiting untuk training.
    
    Struktur folder:
    datasets/species/
    ├── Kepiting Bakau/
    │   ├── img001.jpg
    │   └── ...
    ├── Kepiting Rajungan/
    └── ...
    """

    def __init__(self, image_paths, labels, transform=None):
        self.image_paths = image_paths
        self.labels = labels
        self.transform = transform

    def __len__(self):
        return len(self.image_paths)

    def __getitem__(self, idx):
        img_path = self.image_paths[idx]
        label = self.labels[idx]

        img = cv2.imread(str(img_path))
        if img is None:
            img = np.zeros((224, 224, 3), dtype=np.uint8)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        if self.transform:
            img = self.transform(img)

        return img, label


def get_transforms(augment: bool = True):
    """Get data transforms with augmentation for training."""
    train_transform = transforms.Compose([
        transforms.ToPILImage(),
        transforms.Resize((CONFIG["img_size"] + 32, CONFIG["img_size"] + 32)),
        transforms.RandomCrop(CONFIG["img_size"]),
        transforms.RandomHorizontalFlip(),
        transforms.RandomVerticalFlip(),
        transforms.ColorJitter(brightness=0.3, contrast=0.3, saturation=0.3, hue=0.1),
        transforms.RandomRotation(30),
        transforms.RandomGrayscale(p=0.1),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ]) if augment else get_val_transform()

    return train_transform


def get_val_transform():
    return transforms.Compose([
        transforms.ToPILImage(),
        transforms.Resize((CONFIG["img_size"], CONFIG["img_size"])),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])


def load_dataset(dataset_dir: str):
    """Load semua image paths dan labels dari folder dataset."""
    dataset_path = Path(dataset_dir)
    class_names = CONFIG["class_names"]

    all_paths = []
    all_labels = []
    class_counts = {}

    for class_idx, class_name in enumerate(class_names):
        class_dir = dataset_path / class_name
        if not class_dir.exists():
            logger.warning(f"Class directory not found: {class_dir}")
            continue

        images = list(class_dir.glob("*.jpg")) + list(class_dir.glob("*.png"))
        all_paths.extend(images)
        all_labels.extend([class_idx] * len(images))
        class_counts[class_name] = len(images)
        logger.info(f"  {class_name}: {len(images)} images")

    logger.info(f"Total: {len(all_paths)} images across {len(class_counts)} classes")
    return all_paths, all_labels, class_counts


def build_model(num_classes: int, pretrained: bool = True) -> nn.Module:
    """Build EfficientNet-B0 with custom classification head."""
    model = models.efficientnet_b0(
        weights=models.EfficientNet_B0_Weights.IMAGENET1K_V1 if pretrained else None
    )

    # Freeze backbone initially
    for param in model.features.parameters():
        param.requires_grad = False

    # Replace classifier
    in_features = model.classifier[1].in_features
    model.classifier = nn.Sequential(
        nn.Dropout(p=0.3),
        nn.Linear(in_features, 256),
        nn.ReLU(),
        nn.Dropout(p=0.2),
        nn.Linear(256, num_classes),
    )

    return model


def train_epoch(model, loader, optimizer, criterion, device) -> dict:
    """Train for one epoch."""
    model.train()
    total_loss = 0
    correct = 0
    total = 0

    for batch_idx, (images, labels) in enumerate(loader):
        images = images.to(device)
        labels = labels.to(device)

        optimizer.zero_grad()
        outputs = model(images)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()

        total_loss += loss.item()
        _, predicted = outputs.max(1)
        total += labels.size(0)
        correct += predicted.eq(labels).sum().item()

        if batch_idx % 10 == 0:
            logger.info(
                f"  Batch {batch_idx}/{len(loader)} — "
                f"Loss: {loss.item():.4f} — "
                f"Acc: {100.*correct/total:.1f}%"
            )

    return {
        "loss": total_loss / len(loader),
        "accuracy": 100.0 * correct / total,
    }


def validate_epoch(model, loader, criterion, device) -> dict:
    """Validate for one epoch."""
    model.eval()
    total_loss = 0
    correct = 0
    total = 0
    class_correct = [0] * CONFIG["num_classes"]
    class_total = [0] * CONFIG["num_classes"]

    with torch.no_grad():
        for images, labels in loader:
            images = images.to(device)
            labels = labels.to(device)

            outputs = model(images)
            loss = criterion(outputs, labels)

            total_loss += loss.item()
            _, predicted = outputs.max(1)
            total += labels.size(0)
            correct += predicted.eq(labels).sum().item()

            for i in range(len(labels)):
                label = labels[i].item()
                class_correct[label] += (predicted[i] == labels[i]).item()
                class_total[label] += 1

    per_class_acc = {}
    for i, class_name in enumerate(CONFIG["class_names"]):
        if class_total[i] > 0:
            per_class_acc[class_name] = round(100.0 * class_correct[i] / class_total[i], 1)

    return {
        "loss": total_loss / len(loader),
        "accuracy": 100.0 * correct / total,
        "per_class_accuracy": per_class_acc,
    }


def train():
    """Main training function."""
    device = torch.device(CONFIG["device"])
    logger.info(f"🚀 Training on: {device}")
    logger.info(f"Config: {json.dumps(CONFIG, indent=2)}")

    # Load data
    logger.info("\n📂 Loading dataset...")
    all_paths, all_labels, class_counts = load_dataset(CONFIG["dataset_dir"])

    if len(all_paths) == 0:
        logger.error("No training data found! Please add images to datasets/species/")
        logger.info("Expected structure:")
        for cls in CONFIG["class_names"]:
            logger.info(f"  datasets/species/{cls}/image001.jpg")
        return

    # Split train/val
    from sklearn.model_selection import train_test_split
    X_train, X_val, y_train, y_val = train_test_split(
        all_paths, all_labels,
        test_size=CONFIG["val_split"],
        stratify=all_labels,
        random_state=42,
    )

    # Datasets
    train_dataset = CrabDataset(X_train, y_train, transform=get_transforms(augment=True))
    val_dataset = CrabDataset(X_val, y_val, transform=get_val_transform())

    train_loader = DataLoader(
        train_dataset, batch_size=CONFIG["batch_size"],
        shuffle=True, num_workers=CONFIG["num_workers"], pin_memory=True
    )
    val_loader = DataLoader(
        val_dataset, batch_size=CONFIG["batch_size"],
        shuffle=False, num_workers=CONFIG["num_workers"]
    )

    logger.info(f"Train: {len(X_train)} | Val: {len(X_val)}")

    # Build model
    logger.info("\n🧠 Building model...")
    model = build_model(num_classes=CONFIG["num_classes"])
    model = model.to(device)

    # Optimizer with weight decay
    optimizer = optim.AdamW(
        model.parameters(),
        lr=CONFIG["learning_rate"],
        weight_decay=CONFIG["weight_decay"],
    )

    # Learning rate scheduler
    scheduler = optim.lr_scheduler.CosineAnnealingLR(
        optimizer, T_max=CONFIG["epochs"], eta_min=1e-6
    )

    # Loss with label smoothing
    criterion = nn.CrossEntropyLoss(label_smoothing=0.1)

    # Training loop
    best_val_acc = 0
    best_epoch = 0
    patience_counter = 0
    history = {"train_loss": [], "train_acc": [], "val_loss": [], "val_acc": []}

    logger.info(f"\n🏋️ Starting training for {CONFIG['epochs']} epochs...")

    for epoch in range(1, CONFIG["epochs"] + 1):
        epoch_start = time.time()

        # Unfreeze backbone after epoch 10
        if epoch == 10:
            for param in model.features.parameters():
                param.requires_grad = True
            logger.info("✅ Backbone unfrozen for full fine-tuning")

        logger.info(f"\n── Epoch {epoch}/{CONFIG['epochs']} ──")
        train_metrics = train_epoch(model, train_loader, optimizer, criterion, device)
        val_metrics = validate_epoch(model, val_loader, criterion, device)
        scheduler.step()

        history["train_loss"].append(train_metrics["loss"])
        history["train_acc"].append(train_metrics["accuracy"])
        history["val_loss"].append(val_metrics["loss"])
        history["val_acc"].append(val_metrics["accuracy"])

        epoch_time = time.time() - epoch_start
        logger.info(
            f"Train — Loss: {train_metrics['loss']:.4f}, Acc: {train_metrics['accuracy']:.1f}%\n"
            f"Val   — Loss: {val_metrics['loss']:.4f}, Acc: {val_metrics['accuracy']:.1f}%\n"
            f"Per-class: {val_metrics['per_class_accuracy']}\n"
            f"Time: {epoch_time:.1f}s | LR: {scheduler.get_last_lr()[0]:.6f}"
        )

        # Save best model
        if val_metrics["accuracy"] > best_val_acc:
            best_val_acc = val_metrics["accuracy"]
            best_epoch = epoch
            patience_counter = 0

            os.makedirs(CONFIG["output_dir"], exist_ok=True)
            model_path = os.path.join(CONFIG["output_dir"], CONFIG["model_name"])
            torch.save(model, model_path)
            logger.info(f"✅ Best model saved: {model_path} (acc: {best_val_acc:.1f}%)")

            # Export to ONNX
            _export_onnx(model, model_path.replace(".pt", ".onnx"), device)
        else:
            patience_counter += 1
            if patience_counter >= CONFIG["patience"]:
                logger.info(f"Early stopping triggered at epoch {epoch}")
                break

    logger.info(f"\n🎉 Training complete!")
    logger.info(f"Best epoch: {best_epoch} | Best val accuracy: {best_val_acc:.1f}%")

    # Save training history
    history_path = os.path.join(CONFIG["output_dir"], "training_history.json")
    with open(history_path, "w") as f:
        json.dump(history, f, indent=2)
    logger.info(f"Training history saved: {history_path}")


def _export_onnx(model: nn.Module, output_path: str, device):
    """Export model to ONNX format for faster inference."""
    try:
        dummy_input = torch.randn(1, 3, CONFIG["img_size"], CONFIG["img_size"]).to(device)
        torch.onnx.export(
            model,
            dummy_input,
            output_path,
            opset_version=12,
            input_names=["image"],
            output_names=["logits"],
            dynamic_axes={"image": {0: "batch_size"}, "logits": {0: "batch_size"}},
        )
        logger.info(f"✅ ONNX exported: {output_path}")
    except Exception as e:
        logger.warning(f"ONNX export failed: {e}")


if __name__ == "__main__":
    train()
