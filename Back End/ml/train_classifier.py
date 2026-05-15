"""
Option 2 — Email Pre-classifier Training Script
================================================
Trains a calibrated logistic regression on TF-IDF features to predict
whether an email is an opportunity (1) or not (0).

Run from Back End directory:
    python ml/train_classifier.py

Outputs:
    ml/email_classifier.joblib
    ml/vectorizer_text.joblib
    ml/optimal_threshold.json
"""

import json
import os
import sys

import joblib
import numpy as np
import pandas as pd
import scipy.sparse
from sklearn.calibration import CalibratedClassifierCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    classification_report,
    precision_recall_curve,
    roc_auc_score,
    confusion_matrix,
)
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split

# ── Paths ──────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, "database", "email_labels.csv")
ML_DIR = os.path.join(BASE_DIR, "ml")

CLASSIFIER_PATH = os.path.join(ML_DIR, "email_classifier.joblib")
VECTORIZER_PATH = os.path.join(ML_DIR, "vectorizer_text.joblib")
THRESHOLD_PATH = os.path.join(ML_DIR, "optimal_threshold.json")


def load_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    # Validate required columns
    if "text" not in df.columns or "label" not in df.columns:
        raise ValueError(f"CSV must have 'text' and 'label' columns. Found: {list(df.columns)}")
    df = df.dropna(subset=["text", "label"])
    df["label"] = df["label"].astype(int)
    print(f"Loaded {len(df)} rows — class distribution:")
    print(df["label"].value_counts().to_string())
    return df


def build_features(df: pd.DataFrame, text_vec=None, fit: bool = True):
    """
    Build feature matrix from text + character length.
    No sender column in this dataset, so we use:
      - TF-IDF on text (bigrams, sublinear_tf)
      - Character length as a numeric feature
    """
    # Character length feature
    char_lengths = df["text"].str.len().fillna(0).values.reshape(-1, 1)
    X_numeric = scipy.sparse.csr_matrix(char_lengths)

    # TF-IDF text features
    if fit:
        text_vec = TfidfVectorizer(
            ngram_range=(1, 2),
            sublinear_tf=True,
            max_features=8000,
            min_df=2,
            strip_accents="unicode",
            analyzer="word",
        )
        X_text = text_vec.fit_transform(df["text"])
    else:
        X_text = text_vec.transform(df["text"])

    # Stack text + numeric
    X = scipy.sparse.hstack([X_text, X_numeric])
    return X, text_vec


def find_optimal_threshold(model, X_test, y_test, min_precision: float = 0.95) -> float:
    """
    Find the threshold where precision for class-0 (not-opportunity) >= min_precision.
    This ensures when we skip an LLM call, we're almost never wrong.
    """
    # Probability of class-0
    probs_class0 = model.predict_proba(X_test)[:, 0]
    # Treat class-0 as "positive" for this curve
    precision, recall, thresholds = precision_recall_curve(1 - y_test, probs_class0)

    # Find lowest threshold where precision >= min_precision
    valid = np.where(precision >= min_precision)[0]
    if len(valid) == 0:
        print(f"  Warning: precision never reaches {min_precision:.0%} — using 0.90 fallback")
        return 0.90

    # thresholds has one fewer element than precision/recall
    idx = valid[0]
    if idx >= len(thresholds):
        idx = len(thresholds) - 1

    threshold = float(thresholds[idx])
    print(f"  Optimal threshold: {threshold:.4f}  "
          f"(precision={precision[idx]:.3f}, recall={recall[idx]:.3f})")
    return threshold


def evaluate(model, X_test, y_test, threshold: float):
    print("\n── Standard threshold (0.5) ──")
    y_pred = model.predict(X_test)
    print(classification_report(y_test, y_pred, target_names=["not-opportunity", "opportunity"]))

    print(f"\n── Optimal threshold ({threshold:.4f}) ──")
    probs = model.predict_proba(X_test)[:, 1]
    y_pred_thresh = (probs >= threshold).astype(int)
    print(classification_report(y_test, y_pred_thresh, target_names=["not-opportunity", "opportunity"]))

    print(f"ROC-AUC: {roc_auc_score(y_test, probs):.4f}")
    print(f"Confusion matrix (optimal threshold):\n{confusion_matrix(y_test, y_pred_thresh)}")


def train():
    print("=" * 60)
    print("Option 2 — Email Pre-classifier Training")
    print("=" * 60)

    # 1. Load
    df = load_data(DATA_PATH)

    # 2. Features
    X, text_vec = build_features(df, fit=True)
    y = df["label"].values

    # 3. Train/test split — stratified to preserve class balance
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    print(f"\nTrain: {X_train.shape[0]} samples | Test: {X_test.shape[0]} samples")

    # 4. Cross-validation on training set
    print("\nRunning 5-fold cross-validation...")
    base_lr = LogisticRegression(max_iter=1000, C=1.0, class_weight="balanced", random_state=42)
    cv_scores = cross_val_score(base_lr, X_train, y_train, cv=5, scoring="f1")
    print(f"  CV F1 scores: {cv_scores.round(4)}")
    print(f"  Mean CV F1:   {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")

    # 5. Train calibrated model on full training set
    print("\nTraining calibrated logistic regression...")
    base_lr = LogisticRegression(max_iter=1000, C=1.0, class_weight="balanced", random_state=42)
    model = CalibratedClassifierCV(base_lr, cv=5, method="sigmoid")
    model.fit(X_train, y_train)

    # 6. Find optimal threshold
    print("\nFinding optimal threshold (precision for class-0 >= 95%)...")
    threshold = find_optimal_threshold(model, X_test, y_test, min_precision=0.95)

    # 7. Evaluate
    evaluate(model, X_test, y_test, threshold)

    # 8. Save
    joblib.dump(model, CLASSIFIER_PATH)
    joblib.dump(text_vec, VECTORIZER_PATH)
    json.dump({"threshold": threshold}, open(THRESHOLD_PATH, "w"))

    print(f"\n✓ Saved: {CLASSIFIER_PATH}")
    print(f"✓ Saved: {VECTORIZER_PATH}")
    print(f"✓ Saved: {THRESHOLD_PATH}")
    print("\nDone.")


if __name__ == "__main__":
    train()
