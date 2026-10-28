"""
Unit and Regression Tests for Phase 4 Fine-Tuning Pipeline.
==========================================================
Tests dataset inspection, corrupt file quarantine, duplicate leakage prevention,
deterministic splitting, training smoke execution, and held-out test evaluation.
"""

import io
import json
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from dataset_inspector import compute_file_hash, inspect_dataset, split_dataset
from evaluate_classifier import (
    calculate_metrics_from_confusion_matrix,
    evaluate_checkpoint,
    evaluate_model,
)
from train_classifier import build_model, train_model


def create_dummy_image(color=(200, 100, 50), size=(100, 100)) -> bytes:
    """Generates synthetic JPEG bytes for test fixtures."""
    img = Image.new("RGB", size, color=color)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=90)
    return buf.getvalue()


@pytest.fixture
def mock_dataset_dir(tmp_path):
    """Creates a temporary, self-contained miniature dataset with 2 classes."""
    data_dir = tmp_path / "raw_food_dataset"
    data_dir.mkdir()

    class_a = data_dir / "fresh_apple"
    class_b = data_dir / "fresh_banana"
    class_a.mkdir()
    class_b.mkdir()

    # Create 6 distinct images per class
    for i in range(6):
        img_a = create_dummy_image(color=(200, 50 + i * 10, 50))
        img_b = create_dummy_image(color=(220, 200, 50 + i * 10))
        (class_a / f"apple_{i}.jpg").write_bytes(img_a)
        (class_b / f"banana_{i}.jpg").write_bytes(img_b)

    return data_dir


def test_dataset_inspector_clean_dataset(mock_dataset_dir):
    report = inspect_dataset(mock_dataset_dir)
    assert report.is_valid is True
    assert report.valid_images_count == 12
    assert report.total_files_scanned == 12
    assert set(report.classes) == {"fresh_apple", "fresh_banana"}
    assert report.class_counts["fresh_apple"] == 6
    assert report.class_counts["fresh_banana"] == 6
    assert report.imbalance_ratio == 1.0
    assert len(report.corrupt_files) == 0
    assert len(report.unsupported_files) == 0


def test_dataset_inspector_corrupt_and_unsupported(mock_dataset_dir):
    # Add a corrupt image and a text file
    corrupt_file = mock_dataset_dir / "fresh_apple" / "corrupt.jpg"
    corrupt_file.write_bytes(b"not-an-image-binary-garbage")

    text_file = mock_dataset_dir / "fresh_apple" / "readme.txt"
    text_file.write_text("dataset info")

    report = inspect_dataset(mock_dataset_dir)
    assert report.total_files_scanned == 14
    assert len(report.corrupt_files) == 1
    assert "corrupt.jpg" in report.corrupt_files[0]["path"]
    assert len(report.unsupported_files) == 1
    assert "readme.txt" in report.unsupported_files[0]
    assert report.class_counts["fresh_apple"] == 6


def test_dataset_inspector_duplicate_detection(mock_dataset_dir):
    # Copy exact duplicate image
    src = mock_dataset_dir / "fresh_apple" / "apple_0.jpg"
    dup = mock_dataset_dir / "fresh_banana" / "apple_duplicate.jpg"
    dup.write_bytes(src.read_bytes())

    report = inspect_dataset(mock_dataset_dir)
    assert len(report.duplicate_files) == 1
    assert "apple_duplicate.jpg" in report.duplicate_files[0]["duplicate_file"]


def test_deterministic_splitting_and_zero_leakage(mock_dataset_dir, tmp_path):
    out_dir_1 = tmp_path / "splits_seed_42"
    out_dir_2 = tmp_path / "splits_seed_42_repeat"

    manifest_1 = split_dataset(mock_dataset_dir, out_dir_1, seed=42)
    manifest_2 = split_dataset(mock_dataset_dir, out_dir_2, seed=42)

    assert manifest_1["leakage_free_verified"] is True
    assert manifest_1["total_train_samples"] > 0
    assert manifest_1["total_val_samples"] > 0
    assert manifest_1["total_test_samples"] > 0

    # Verify zero leakage by checking file hashes across split folders
    train_hashes = {compute_file_hash(p) for p in (out_dir_1 / "train").rglob("*.jpg")}
    val_hashes = {compute_file_hash(p) for p in (out_dir_1 / "val").rglob("*.jpg")}
    test_hashes = {compute_file_hash(p) for p in (out_dir_1 / "test").rglob("*.jpg")}

    assert len(train_hashes & val_hashes) == 0, "Train-Val leakage detected!"
    assert len(train_hashes & test_hashes) == 0, "Train-Test leakage detected!"
    assert len(val_hashes & test_hashes) == 0, "Val-Test leakage detected!"

    # Determinism: identical files partitioned into train
    train_files_1 = sorted([p.name for p in (out_dir_1 / "train").rglob("*.jpg")])
    train_files_2 = sorted([p.name for p in (out_dir_2 / "train").rglob("*.jpg")])
    assert train_files_1 == train_files_2


def test_training_smoke_test_cpu(mock_dataset_dir, tmp_path):
    splits_dir = tmp_path / "dataset_splits"
    split_dataset(mock_dataset_dir, splits_dir, seed=42)

    checkpoint_dir = tmp_path / "checkpoint_out"
    meta = train_model(
        data_dir=splits_dir,
        output_dir=checkpoint_dir,
        backbone="mobilenet_v3_small",
        epochs=1,
        batch_size=4,
        device="cpu",
        smoke_test=True,
    )

    assert meta["smoke_test"] is True
    assert meta["num_classes"] == 2
    assert (checkpoint_dir / "best_checkpoint.pt").exists()
    assert (checkpoint_dir / "class_mapping.json").exists()
    assert (checkpoint_dir / "preprocessing_config.json").exists()
    assert (checkpoint_dir / "training_metadata.json").exists()

    with open(checkpoint_dir / "class_mapping.json") as f:
        mapping = json.load(f)
    assert len(mapping["id2label"]) == 2


def test_confusion_matrix_and_metrics_calculation():
    # Synthetic 3-class confusion matrix
    # Class 0: 8 correct, 1 mistaken as 1, 1 mistaken as 2 -> TP=8, total=10
    # Class 1: 0 mistaken as 0, 9 correct, 1 mistaken as 2 -> TP=9, total=10
    # Class 2: 2 mistaken as 0, 1 mistaken as 1, 7 correct -> TP=7, total=10
    cm = np.array([
        [8, 1, 1],
        [0, 9, 1],
        [2, 1, 7],
    ])
    classes = ["apple", "banana", "orange"]

    metrics = calculate_metrics_from_confusion_matrix(cm, classes)
    assert metrics["total_test_samples"] == 30
    assert metrics["accuracy"] == round(24 / 30, 4)
    assert 0.0 <= metrics["macro_precision"] <= 1.0
    assert 0.0 <= metrics["macro_recall"] <= 1.0
    assert 0.0 <= metrics["macro_f1"] <= 1.0
    assert metrics["per_class"]["apple"]["support"] == 10
    assert metrics["per_class"]["banana"]["support"] == 10
    assert metrics["per_class"]["orange"]["support"] == 10


def test_evaluation_on_held_out_test_set(mock_dataset_dir, tmp_path):
    splits_dir = tmp_path / "splits_for_eval"
    split_dataset(mock_dataset_dir, splits_dir, seed=42)

    checkpoint_dir = tmp_path / "ckpt_for_eval"
    train_model(
        data_dir=splits_dir,
        output_dir=checkpoint_dir,
        epochs=1,
        smoke_test=True,
        device="cpu",
    )

    report_out = tmp_path / "evaluation_report.json"
    results = evaluate_checkpoint(
        checkpoint_path=checkpoint_dir / "best_checkpoint.pt",
        test_dir=splits_dir / "test",
        output_report_path=report_out,
        device="cpu",
    )

    assert "summary_metrics" in results
    assert "accuracy" in results["summary_metrics"]
    assert "macro_f1" in results["summary_metrics"]
    assert "confusion_matrix" in results
    assert len(results["confusion_matrix"]) == 2
    assert report_out.exists()


def test_evaluation_fails_on_empty_test_set(tmp_path):
    empty_dir = tmp_path / "empty_test_folder"
    empty_dir.mkdir()

    mapping_file = tmp_path / "class_mapping.json"
    mapping_file.write_text(json.dumps({
        "id2label": {"0": "cat", "1": "dog"},
        "label2id": {"cat": 0, "dog": 1},
    }))

    model = build_model("mobilenet_v3_small", num_classes=2, pretrained=False)

    with pytest.raises(ValueError, match="No test images found"):
        evaluate_model(model, empty_dir, mapping_file, device="cpu")
