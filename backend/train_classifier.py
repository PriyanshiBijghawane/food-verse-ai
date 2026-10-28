"""
Reproducible Transfer-Learning Fine-Tuning Pipeline for Food Verse AI.
======================================================================
Phase 4: Standalone training pipeline using transfer learning.
Configurable for CPU execution, deterministic seed, early checkpointing,
and structured metadata logging. Completely decoupled from FastAPI.
"""

from __future__ import annotations

import argparse
import datetime
import json
import logging
import os
import random
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from torchvision import datasets, models, transforms

from evaluate_classifier import evaluate_model

logger = logging.getLogger("food_verse_ai.trainer")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def set_seed(seed: int = 42) -> None:
    """Sets random seeds across Python, NumPy, and PyTorch for deterministic training."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False


def build_model(
    backbone_name: str = "mobilenet_v3_small",
    num_classes: int = 2,
    pretrained: bool = True,
    freeze_backbone: bool = True,
) -> nn.Module:
    """
    Builds a transfer-learning model.
    Freezes the backbone feature extractor and attaches a custom classification head.
    """
    if backbone_name == "mobilenet_v3_small":
        weights = models.MobileNet_V3_Small_Weights.DEFAULT if pretrained else None
        model = models.mobilenet_v3_small(weights=weights)
        if freeze_backbone and pretrained:
            for param in model.features.parameters():
                param.requires_grad = False
        in_features = model.classifier[3].in_features
        model.classifier[3] = nn.Linear(in_features, num_classes)

    elif backbone_name == "resnet18":
        weights = models.ResNet18_Weights.DEFAULT if pretrained else None
        model = models.resnet18(weights=weights)
        if freeze_backbone and pretrained:
            for param in model.parameters():
                param.requires_grad = False
        in_features = model.fc.in_features
        model.fc = nn.Linear(in_features, num_classes)
        for param in model.fc.parameters():
            param.requires_grad = True

    else:
        raise ValueError(f"Unsupported backbone '{backbone_name}'. Choose 'mobilenet_v3_small' or 'resnet18'.")

    return model


def get_data_transforms() -> Tuple[transforms.Compose, transforms.Compose]:
    """Returns standardized training and validation image transformations."""
    train_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.RandomHorizontalFlip(p=0.5),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])
    val_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])
    return train_transform, val_transform


def train_model(
    data_dir: Path | str,
    output_dir: Path | str,
    backbone: str = "mobilenet_v3_small",
    epochs: int = 3,
    batch_size: int = 16,
    lr: float = 1e-3,
    seed: int = 42,
    device: Optional[str] = None,
    smoke_test: bool = False,
    workers: int = 0,
) -> Dict[str, Any]:
    """
    Executes a transfer learning training cycle.
    Expected data_dir layout:
      data_dir/train/<class_names>/<images>
      data_dir/val/<class_names>/<images>
      data_dir/test/<class_names>/<images>
    """
    set_seed(seed)
    data_path = Path(data_dir)
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    if device is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"

    train_dir = data_path / "train"
    val_dir = data_path / "val"
    test_dir = data_path / "test"

    if not train_dir.exists() or not val_dir.exists():
        raise FileNotFoundError(
            f"Expected train and val directories in '{data_path}'. "
            "Please run dataset_inspector.py --split first."
        )

    train_transform, val_transform = get_data_transforms()

    train_dataset = datasets.ImageFolder(train_dir, transform=train_transform)
    val_dataset = datasets.ImageFolder(val_dir, transform=val_transform)

    classes = train_dataset.classes
    num_classes = len(classes)
    if num_classes < 2:
        raise ValueError(f"Training requires >= 2 classes, found {num_classes} ({classes}).")

    id2label = {i: c for i, c in enumerate(classes)}
    label2id = {c: i for i, c in enumerate(classes)}

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, num_workers=workers)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False, num_workers=workers)

    logger.info("Initializing %s transfer learning model for %d classes...", backbone, num_classes)
    model = build_model(backbone_name=backbone, num_classes=num_classes, pretrained=True, freeze_backbone=True)
    model.to(device)

    criterion = nn.CrossEntropyLoss()
    trainable_params = [p for p in model.parameters() if p.requires_grad]
    optimizer = optim.Adam(trainable_params, lr=lr)

    history: List[Dict[str, Any]] = []
    best_val_acc = -1.0
    best_checkpoint_path = out_path / "best_checkpoint.pt"

    start_time = datetime.datetime.now(datetime.timezone.utc)
    logger.info("Starting training loop on device '%s' (smoke_test=%s)...", device, smoke_test)

    num_epochs = 1 if smoke_test else epochs

    for epoch in range(1, num_epochs + 1):
        # 1. Training Phase
        model.train()
        running_loss = 0.0
        correct_train = 0
        total_train = 0

        for step, (inputs, targets) in enumerate(train_loader):
            inputs, targets = inputs.to(device), targets.to(device)

            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs, targets)
            loss.backward()
            optimizer.step()

            running_loss += loss.item() * inputs.size(0)
            preds = torch.argmax(outputs, dim=1)
            correct_train += int((preds == targets).sum().item())
            total_train += targets.size(0)

            if smoke_test:
                logger.info("Smoke test: completed 1 training mini-batch step.")
                break

        epoch_train_loss = running_loss / max(1, total_train)
        epoch_train_acc = correct_train / max(1, total_train)

        # 2. Validation Phase
        model.eval()
        val_loss = 0.0
        correct_val = 0
        total_val = 0

        with torch.no_grad():
            for step, (inputs, targets) in enumerate(val_loader):
                inputs, targets = inputs.to(device), targets.to(device)
                outputs = model(inputs)
                loss = criterion(outputs, targets)

                val_loss += loss.item() * inputs.size(0)
                preds = torch.argmax(outputs, dim=1)
                correct_val += int((preds == targets).sum().item())
                total_val += targets.size(0)

                if smoke_test:
                    logger.info("Smoke test: completed 1 validation mini-batch step.")
                    break

        epoch_val_loss = val_loss / max(1, total_val)
        epoch_val_acc = correct_val / max(1, total_val)

        logger.info(
            "Epoch %d/%d — Train Loss: %.4f, Train Acc: %.2f%% | Val Loss: %.4f, Val Acc: %.2f%%",
            epoch, num_epochs, epoch_train_loss, epoch_train_acc * 100, epoch_val_loss, epoch_val_acc * 100
        )

        epoch_stats = {
            "epoch": epoch,
            "train_loss": round(epoch_train_loss, 4),
            "train_acc": round(epoch_train_acc, 4),
            "val_loss": round(epoch_val_loss, 4),
            "val_acc": round(epoch_val_acc, 4),
        }
        history.append(epoch_stats)

        # Save best model
        if epoch_val_acc >= best_val_acc:
            best_val_acc = epoch_val_acc
            torch.save({
                "epoch": epoch,
                "model_state_dict": model.state_dict(),
                "optimizer_state_dict": optimizer.state_dict(),
                "best_val_acc": best_val_acc,
                "num_classes": num_classes,
                "backbone": backbone,
                "classes": classes,
            }, best_checkpoint_path)

    end_time = datetime.datetime.now(datetime.timezone.utc)
    duration_sec = round((end_time - start_time).total_seconds(), 2)

    # Save class mapping
    class_mapping = {"id2label": id2label, "label2id": label2id}
    with open(out_path / "class_mapping.json", "w", encoding="utf-8") as f:
        json.dump(class_mapping, f, indent=2)

    # Save preprocessing config
    prep_config = {
        "input_size": [224, 224],
        "image_mean": [0.485, 0.456, 0.406],
        "image_std": [0.229, 0.224, 0.225],
        "resample": "BILINEAR",
        "crop_pct": 0.875,
    }
    with open(out_path / "preprocessing_config.json", "w", encoding="utf-8") as f:
        json.dump(prep_config, f, indent=2)

    # Optional held-out test evaluation if test_dir exists
    test_eval = None
    if test_dir.exists():
        try:
            logger.info("Evaluating best checkpoint on held-out test split...")
            test_eval = evaluate_model(
                model=model,
                test_dir=test_dir,
                class_mapping_path=out_path / "class_mapping.json",
                device=device,
            )
            with open(out_path / "test_evaluation.json", "w", encoding="utf-8") as f:
                json.dump(test_eval, f, indent=2)
        except Exception as eval_exc:
            logger.warning("Could not run post-training test evaluation: %s", eval_exc)

    # Save training metadata
    metadata = {
        "training_timestamp": start_time.isoformat(),
        "training_duration_seconds": duration_sec,
        "backbone": backbone,
        "device": device,
        "seed": seed,
        "epochs": num_epochs,
        "batch_size": batch_size,
        "learning_rate": lr,
        "smoke_test": smoke_test,
        "num_classes": num_classes,
        "classes": classes,
        "train_samples": len(train_dataset),
        "val_samples": len(val_dataset),
        "best_val_acc": round(best_val_acc, 4),
        "training_history": history,
        "held_out_test_metrics": test_eval["summary_metrics"] if test_eval else None,
    }
    with open(out_path / "training_metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    logger.info("Training pipeline completed. Artifacts saved in '%s'.", out_path)
    return metadata


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Transfer learning training pipeline for Food Verse AI.")
    parser.add_argument("--data_dir", type=str, required=True, help="Directory containing train, val, and test splits.")
    parser.add_argument("--output_dir", type=str, default="checkpoints/transfer_run", help="Output directory for checkpoints.")
    parser.add_argument("--backbone", type=str, default="mobilenet_v3_small", choices=["mobilenet_v3_small", "resnet18"])
    parser.add_argument("--epochs", type=int, default=3, help="Number of training epochs.")
    parser.add_argument("--batch_size", type=int, default=16, help="Batch size.")
    parser.add_argument("--lr", type=float, default=1e-3, help="Learning rate.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed.")
    parser.add_argument("--device", type=str, default="cpu", help="Device (cpu or cuda).")
    parser.add_argument("--smoke_test", action="store_true", help="Run 1 mini-batch step for quick smoke validation.")
    args = parser.parse_args()

    meta = train_model(
        data_dir=args.data_dir,
        output_dir=args.output_dir,
        backbone=args.backbone,
        epochs=args.epochs,
        batch_size=args.batch_size,
        lr=args.lr,
        seed=args.seed,
        device=args.device,
        smoke_test=args.smoke_test,
    )
    print(json.dumps(meta, indent=2))
