"""
Standalone Model Evaluation Module for Food Verse AI.
=====================================================
Phase 4: Rigorous evaluation on held-out test splits.
Calculates Accuracy, Precision, Recall, Macro F1, and Confusion Matrix.
Never evaluates on training data or tunes thresholds on test sets.
"""

from __future__ import annotations

import argparse
import datetime
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np
import torch
import torch.nn as nn
from PIL import Image
from torch.utils.data import DataLoader, Dataset
from torchvision import models, transforms

logger = logging.getLogger("food_verse_ai.evaluation")


class EvaluationImageDataset(Dataset):
    """Simple, transparent dataset for evaluation."""

    def __init__(self, root_dir: Path | str, class_to_idx: Dict[str, int], transform=None):
        self.root = Path(root_dir)
        self.class_to_idx = class_to_idx
        self.transform = transform
        self.samples: List[Tuple[Path, int]] = []

        for class_name, idx in class_to_idx.items():
            class_folder = self.root / class_name
            if class_folder.exists() and class_folder.is_dir():
                for f in sorted(class_folder.iterdir()):
                    if f.is_file() and f.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp", ".bmp"}:
                        self.samples.append((f, idx))

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, index: int) -> Tuple[torch.Tensor, int]:
        path, target = self.samples[index]
        with Image.open(path) as img:
            img = img.convert("RGB")
        if self.transform:
            img = self.transform(img)
        return img, target


def calculate_metrics_from_confusion_matrix(
    cm: np.ndarray,
    classes: List[str],
) -> Dict[str, Any]:
    """
    Computes accuracy, precision, recall, and F1 from a confusion matrix cm.
    cm[i, j] = count of ground-truth class i predicted as class j.
    """
    num_classes = len(classes)
    total_samples = int(np.sum(cm))
    if total_samples == 0:
        return {
            "accuracy": 0.0,
            "macro_precision": 0.0,
            "macro_recall": 0.0,
            "macro_f1": 0.0,
            "weighted_f1": 0.0,
            "per_class": {},
            "total_test_samples": 0,
        }

    tp = np.diag(cm).astype(float)
    fp = np.sum(cm, axis=0).astype(float) - tp
    fn = np.sum(cm, axis=1).astype(float) - tp
    support = np.sum(cm, axis=1).astype(int)

    precision = np.zeros(num_classes, dtype=float)
    recall = np.zeros(num_classes, dtype=float)
    f1 = np.zeros(num_classes, dtype=float)

    for i in range(num_classes):
        precision[i] = tp[i] / (tp[i] + fp[i]) if (tp[i] + fp[i]) > 0 else 0.0
        recall[i] = tp[i] / (tp[i] + fn[i]) if (tp[i] + fn[i]) > 0 else 0.0
        if precision[i] + recall[i] > 0:
            f1[i] = 2.0 * (precision[i] * recall[i]) / (precision[i] + recall[i])
        else:
            f1[i] = 0.0

    accuracy = float(np.sum(tp) / total_samples)
    macro_p = float(np.mean(precision))
    macro_r = float(np.mean(recall))
    macro_f1 = float(np.mean(f1))

    # Weighted metrics by class support
    weights = support.astype(float) / total_samples
    weighted_f1 = float(np.sum(f1 * weights))

    per_class_report: Dict[str, Dict[str, Any]] = {}
    for i, c_name in enumerate(classes):
        per_class_report[c_name] = {
            "precision": round(float(precision[i]), 4),
            "recall": round(float(recall[i]), 4),
            "f1_score": round(float(f1[i]), 4),
            "support": int(support[i]),
            "true_positives": int(tp[i]),
            "false_positives": int(fp[i]),
            "false_negatives": int(fn[i]),
        }

    return {
        "accuracy": round(accuracy, 4),
        "macro_precision": round(macro_p, 4),
        "macro_recall": round(macro_r, 4),
        "macro_f1": round(macro_f1, 4),
        "weighted_f1": round(weighted_f1, 4),
        "total_test_samples": total_samples,
        "per_class": per_class_report,
    }


def evaluate_model(
    model: nn.Module,
    test_dir: Path | str,
    class_mapping_path: Path | str,
    device: str = "cpu",
    batch_size: int = 16,
) -> Dict[str, Any]:
    """
    Evaluates a PyTorch model on a held-out test directory.
    Requires class_mapping_path to guarantee consistent label index binding.
    """
    test_path = Path(test_dir)
    with open(class_mapping_path, "r", encoding="utf-8") as f:
        mapping = json.load(f)

    id2label = mapping["id2label"]
    label2id = mapping["label2id"]
    # Handle string keys from json
    classes = [id2label[str(i)] if str(i) in id2label else id2label[i] for i in range(len(label2id))]

    eval_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])

    dataset = EvaluationImageDataset(test_path, class_to_idx=label2id, transform=eval_transform)
    if len(dataset) == 0:
        raise ValueError(f"No test images found in '{test_path}' for classes: {classes}")

    loader = DataLoader(dataset, batch_size=batch_size, shuffle=False)

    model.eval()
    model.to(device)

    num_classes = len(classes)
    cm = np.zeros((num_classes, num_classes), dtype=int)

    all_preds: List[int] = []
    all_targets: List[int] = []

    with torch.no_grad():
        for inputs, targets in loader:
            inputs = inputs.to(device)
            targets = targets.to(device)

            outputs = model(inputs)
            preds = torch.argmax(outputs, dim=1)

            for t, p in zip(targets.cpu().numpy(), preds.cpu().numpy()):
                cm[t, p] += 1
                all_targets.append(int(t))
                all_preds.append(int(p))

    metrics = calculate_metrics_from_confusion_matrix(cm, classes)

    return {
        "evaluation_timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "device_used": device,
        "test_dataset_dir": str(test_path),
        "classes": classes,
        "confusion_matrix": cm.tolist(),
        "summary_metrics": {
            "accuracy": metrics["accuracy"],
            "macro_precision": metrics["macro_precision"],
            "macro_recall": metrics["macro_recall"],
            "macro_f1": metrics["macro_f1"],
            "weighted_f1": metrics["weighted_f1"],
            "total_test_samples": metrics["total_test_samples"],
        },
        "per_class_metrics": metrics["per_class"],
    }


def evaluate_checkpoint(
    checkpoint_path: Path | str,
    test_dir: Path | str,
    output_report_path: Optional[Path | str] = None,
    device: str = "cpu",
) -> Dict[str, Any]:
    """Loads a checkpoint and associated class mapping to evaluate on the test split."""
    ckpt_file = Path(checkpoint_path)
    if not ckpt_file.exists():
        raise FileNotFoundError(f"Checkpoint not found at '{ckpt_file}'.")

    checkpoint = torch.load(ckpt_file, map_location=device)
    num_classes = checkpoint.get("num_classes", 2)
    backbone_name = checkpoint.get("backbone", "mobilenet_v3_small")

    # Reconstruct backbone architecture
    if backbone_name == "mobilenet_v3_small":
        model = models.mobilenet_v3_small(weights=None)
        in_features = model.classifier[3].in_features
        model.classifier[3] = nn.Linear(in_features, num_classes)
    elif backbone_name == "resnet18":
        model = models.resnet18(weights=None)
        in_features = model.fc.in_features
        model.fc = nn.Linear(in_features, num_classes)
    else:
        raise ValueError(f"Unsupported backbone '{backbone_name}'.")

    model.load_state_dict(checkpoint["model_state_dict"])

    mapping_file = ckpt_file.parent / "class_mapping.json"
    if not mapping_file.exists():
        raise FileNotFoundError(f"Missing class_mapping.json in checkpoint directory '{ckpt_file.parent}'.")

    results = evaluate_model(
        model=model,
        test_dir=test_dir,
        class_mapping_path=mapping_file,
        device=device,
    )
    results["checkpoint_file"] = str(ckpt_file)
    results["model_backbone"] = backbone_name

    if output_report_path:
        out_p = Path(output_report_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        with open(out_p, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)

    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate a fine-tuned model checkpoint on a held-out test set.")
    parser.add_argument("--checkpoint", type=str, required=True, help="Path to checkpoint.pt.")
    parser.add_argument("--test_dir", type=str, required=True, help="Path to test set directory.")
    parser.add_argument("--output_report", type=str, default="evaluation_report.json", help="Path to save results JSON.")
    parser.add_argument("--device", type=str, default="cpu", help="Device (cpu or cuda).")
    args = parser.parse_args()

    res = evaluate_checkpoint(
        checkpoint_path=args.checkpoint,
        test_dir=args.test_dir,
        output_report_path=args.output_report,
        device=args.device,
    )
    print(json.dumps(res["summary_metrics"], indent=2))
