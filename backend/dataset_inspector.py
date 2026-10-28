"""
Dataset Inspection and Reproducible Splitting Utility for Food Verse AI.
=======================================================================
Phase 4: Dataset inspection, integrity validation, class imbalance reporting,
and leakage-free reproducible train/validation/test splitting.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import random
import shutil
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from PIL import Image, UnidentifiedImageError

logger = logging.getLogger("food_verse_ai.dataset_inspector")

SUPPORTED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}


@dataclass
class DatasetInspectionReport:
    data_dir: str
    is_valid: bool
    total_files_scanned: int
    valid_images_count: int
    corrupt_files: List[Dict[str, str]] = field(default_factory=list)
    unsupported_files: List[str] = field(default_factory=list)
    duplicate_files: List[Dict[str, Any]] = field(default_factory=list)
    classes: List[str] = field(default_factory=list)
    class_counts: Dict[str, int] = field(default_factory=dict)
    min_class_count: int = 0
    max_class_count: int = 0
    median_class_count: float = 0.0
    imbalance_ratio: float = 1.0
    recommendations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def compute_file_hash(file_path: Path) -> str:
    """Computes SHA-256 hash of file content to detect exact image duplicates."""
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def inspect_dataset(data_dir: Path | str) -> DatasetInspectionReport:
    """
    Scans a folder-based image dataset (expected format: `data_dir/<class_name>/<image_file>`).
    Identifies valid images, corrupt files, unsupported formats, duplicate image hashes,
    and calculates class imbalance metrics.
    """
    root = Path(data_dir)
    if not root.exists() or not root.is_dir():
        return DatasetInspectionReport(
            data_dir=str(root),
            is_valid=False,
            total_files_scanned=0,
            valid_images_count=0,
            recommendations=[f"Dataset directory '{root}' does not exist or is not a directory."],
        )

    # Class directories are direct subdirectories of root
    class_dirs = [d for d in root.iterdir() if d.is_dir() and not d.name.startswith(".")]

    if not class_dirs:
        return DatasetInspectionReport(
            data_dir=str(root),
            is_valid=False,
            total_files_scanned=0,
            valid_images_count=0,
            recommendations=[
                "No class subdirectories found. Expected folder structure: "
                f"'{root}/<class_name>/<images...>'"
            ],
        )

    classes = sorted([d.name for d in class_dirs])
    class_counts: Dict[str, int] = {c: 0 for c in classes}
    corrupt_files: List[Dict[str, str]] = []
    unsupported_files: List[str] = []
    seen_hashes: Dict[str, str] = {}  # hash -> first_filepath
    duplicates: List[Dict[str, Any]] = []

    total_scanned = 0

    for c_dir in class_dirs:
        c_name = c_dir.name
        for file_path in c_dir.iterdir():
            if file_path.is_dir() or file_path.name.startswith("."):
                continue

            total_scanned += 1
            ext = file_path.suffix.lower()

            if ext not in SUPPORTED_IMAGE_EXTENSIONS:
                unsupported_files.append(str(file_path))
                continue

            # Verify image file integrity
            try:
                with Image.open(file_path) as img:
                    img.verify()
            except (UnidentifiedImageError, Exception) as exc:
                corrupt_files.append({
                    "path": str(file_path),
                    "error": f"{type(exc).__name__}: {str(exc)}",
                })
                continue

            # Check duplicate content hash
            try:
                f_hash = compute_file_hash(file_path)
                if f_hash in seen_hashes:
                    duplicates.append({
                        "duplicate_file": str(file_path),
                        "original_file": seen_hashes[f_hash],
                        "sha256": f_hash,
                    })
                else:
                    seen_hashes[f_hash] = str(file_path)
                    class_counts[c_name] += 1
            except Exception as exc:
                corrupt_files.append({
                    "path": str(file_path),
                    "error": f"HashingError: {str(exc)}",
                })

    valid_images = sum(class_counts.values())
    counts = [c for c in class_counts.values() if c > 0]
    min_count = min(counts) if counts else 0
    max_count = max(counts) if counts else 0

    if counts:
        sorted_counts = sorted(counts)
        mid = len(sorted_counts) // 2
        median_count = (
            sorted_counts[mid]
            if len(sorted_counts) % 2 != 0
            else (sorted_counts[mid - 1] + sorted_counts[mid]) / 2.0
        )
        imbalance_ratio = round(max_count / max(1, min_count), 2)
    else:
        median_count = 0.0
        imbalance_ratio = 1.0

    recommendations: List[str] = []
    if len(classes) < 2:
        recommendations.append("Classification requires at least 2 distinct classes.")
    if min_count < 10:
        recommendations.append(f"Class '{min(class_counts, key=class_counts.get)}' has fewer than 10 valid images. Recommend collecting more samples.")
    if imbalance_ratio > 3.0:
        recommendations.append(f"High class imbalance detected (ratio: {imbalance_ratio}:1). Consider weighted loss sampling or data augmentation.")
    if corrupt_files:
        recommendations.append(f"Quarantine or remove {len(corrupt_files)} corrupt image file(s) before training.")
    if duplicates:
        recommendations.append(f"Detected {len(duplicates)} duplicate image file(s). Duplicates are deduplicated during dataset splitting to avoid cross-split leakage.")

    is_valid = len(classes) >= 2 and valid_images >= 6 and min_count >= 1

    return DatasetInspectionReport(
        data_dir=str(root),
        is_valid=is_valid,
        total_files_scanned=total_scanned,
        valid_images_count=valid_images,
        corrupt_files=corrupt_files,
        unsupported_files=unsupported_files,
        duplicate_files=duplicates,
        classes=classes,
        class_counts=class_counts,
        min_class_count=min_count,
        max_class_count=max_count,
        median_class_count=median_count,
        imbalance_ratio=imbalance_ratio,
        recommendations=recommendations,
    )


def split_dataset(
    data_dir: Path | str,
    output_dir: Path | str,
    train_ratio: float = 0.70,
    val_ratio: float = 0.15,
    test_ratio: float = 0.15,
    seed: int = 42,
    prevent_leakage: bool = True,
) -> Dict[str, Any]:
    """
    Creates reproducible, deterministic train/val/test splits in `output_dir`.
    Guarantees zero data leakage by:
    1. Quarantining duplicate images by content hash.
    2. Shuffling deterministically with a fixed random seed.
    3. Asserting that no duplicate hash exists across train, val, and test splits.
    """
    if abs((train_ratio + val_ratio + test_ratio) - 1.0) > 1e-4:
        raise ValueError("Ratios train_ratio + val_ratio + test_ratio must sum to 1.0.")

    root = Path(data_dir)
    out = Path(output_dir)

    report = inspect_dataset(root)
    if not report.is_valid:
        raise ValueError(
            f"Dataset at '{root}' is not valid for splitting: {', '.join(report.recommendations)}"
        )

    # Clean / prepare output directory
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True, exist_ok=True)

    splits = ["train", "val", "test"]
    for s in splits:
        for c in report.classes:
            (out / s / c).mkdir(parents=True, exist_ok=True)

    rng = random.Random(seed)
    seen_hashes: Set[str] = set()
    split_hashes: Dict[str, Set[str]] = {"train": set(), "val": set(), "test": set()}
    split_counts: Dict[str, Dict[str, int]] = {s: {c: 0 for c in report.classes} for s in splits}

    for c in report.classes:
        c_dir = root / c
        valid_class_files: List[Path] = []

        for f in sorted(c_dir.iterdir()):
            if f.is_file() and f.suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS:
                try:
                    f_hash = compute_file_hash(f)
                    if prevent_leakage and f_hash in seen_hashes:
                        continue  # Skip duplicate to prevent data leakage
                    seen_hashes.add(f_hash)
                    valid_class_files.append(f)
                except Exception:
                    continue

        # Deterministic shuffle
        rng.shuffle(valid_class_files)
        n = len(valid_class_files)

        n_train = max(1, int(round(n * train_ratio)))
        n_val = max(1, int(round(n * val_ratio))) if n >= 3 else 0
        n_test = n - (n_train + n_val)
        if n_test < 1 and n >= 3:
            # Adjust to ensure at least 1 test sample for evaluation
            n_train = max(1, n_train - 1)
            n_test = 1

        train_files = valid_class_files[:n_train]
        val_files = valid_class_files[n_train:n_train + n_val]
        test_files = valid_class_files[n_train + n_val:]

        for s_name, file_list in [("train", train_files), ("val", val_files), ("test", test_files)]:
            for src in file_list:
                dest = out / s_name / c / src.name
                shutil.copy2(src, dest)
                h = compute_file_hash(src)
                split_hashes[s_name].add(h)
                split_counts[s_name][c] += 1

    # Verification of zero leakage
    train_val_overlap = split_hashes["train"] & split_hashes["val"]
    train_test_overlap = split_hashes["train"] & split_hashes["test"]
    val_test_overlap = split_hashes["val"] & split_hashes["test"]

    has_leakage = bool(train_val_overlap or train_test_overlap or val_test_overlap)
    if has_leakage:
        raise RuntimeError("Data leakage detected between dataset splits during split validation!")

    total_train = sum(split_counts["train"].values())
    total_val = sum(split_counts["val"].values())
    total_test = sum(split_counts["test"].values())

    manifest = {
        "source_dir": str(root),
        "output_dir": str(out),
        "seed": seed,
        "train_ratio": train_ratio,
        "val_ratio": val_ratio,
        "test_ratio": test_ratio,
        "total_train_samples": total_train,
        "total_val_samples": total_val,
        "total_test_samples": total_test,
        "classes": report.classes,
        "per_class_counts": split_counts,
        "leakage_free_verified": not has_leakage,
    }

    with open(out / "split_manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Inspect and split image datasets.")
    parser.add_argument("--data_dir", type=str, required=True, help="Path to raw dataset directory.")
    parser.add_argument("--split", action="store_true", help="Generate train/val/test splits.")
    parser.add_argument("--output_dir", type=str, default="data/dataset_splits", help="Output directory for splits.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for splitting.")
    args = parser.parse_args()

    report = inspect_dataset(args.data_dir)
    print(json.dumps(report.to_dict(), indent=2))

    if args.split:
        manifest = split_dataset(args.data_dir, args.output_dir, seed=args.seed)
        print(f"\nSplit completed successfully into '{args.output_dir}'")
