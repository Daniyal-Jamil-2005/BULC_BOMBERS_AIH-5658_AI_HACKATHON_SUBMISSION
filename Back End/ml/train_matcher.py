"""
Option 4 — Student-Opportunity Match Scorer Training Script
============================================================
Trains a GradientBoostingRegressor to predict match score (0.0–1.0)
for a (student_profile, opportunity) pair.

Run from Back End directory:
    python ml/train_matcher.py

Outputs:
    ml/match_scorer.joblib
    ml/feature_names.json
"""

import json
import os

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import cross_val_score, train_test_split

# ── Paths ──────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, "database", "match_scores.csv")
ML_DIR = os.path.join(BASE_DIR, "ml")

SCORER_PATH = os.path.join(ML_DIR, "match_scorer.joblib")
FEATURES_PATH = os.path.join(ML_DIR, "feature_names.json")

# Features to use for training
# quality_signal is included — it's a composite signal in the dataset
FEATURE_COLS = [
    "cgpa_gap",
    "skills_overlap_pct",
    "location_match",
    "type_preference_match",
    "graduation_year_match",
    "financial_need",
    "is_scholarship",
    "urgency_score",
    "quality_signal",
    # Explicit interaction terms (computed below)
    "cgpa_x_skills",
    "financial_x_scholarship",
]

# Human-readable labels for UI explainability
REASON_LABELS = {
    "skills_overlap_pct":     "Strong skill overlap",
    "cgpa_gap":               "CGPA requirement cleared",
    "urgency_score":          "Deadline approaching",
    "type_preference_match":  "Matches your preferred type",
    "location_match":         "Location match",
    "financial_need":         "Financial need considered",
    "is_scholarship":         "Scholarship opportunity",
    "graduation_year_match":  "Graduation year match",
    "quality_signal":         "High quality opportunity signal",
    "cgpa_x_skills":          "Strong combined profile fit",
    "financial_x_scholarship": "Financial need + scholarship bonus",
}


def load_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    print(f"Loaded {len(df)} rows")
    print(f"Columns: {list(df.columns)}")
    print(f"\nmatch_score stats:\n{df['match_score'].describe().round(4).to_string()}")
    return df


def add_interaction_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add explicit interaction terms that help the model.
    cgpa_gap * skills_overlap_pct: a student who misses CGPA but has 80% skill overlap
    is very different from one who meets CGPA but has 10% overlap.
    """
    df = df.copy()
    df["cgpa_x_skills"] = df["cgpa_gap"] * df["skills_overlap_pct"]
    df["financial_x_scholarship"] = df["financial_need"] * df["is_scholarship"]
    return df


def check_score_distribution(y: np.ndarray):
    """Warn if scores are bimodal — should be roughly normal 0.3–0.8."""
    low = (y < 0.2).mean()
    high = (y > 0.8).mean()
    mid = ((y >= 0.2) & (y <= 0.8)).mean()
    print(f"\nScore distribution:")
    print(f"  < 0.2  : {low:.1%}")
    print(f"  0.2–0.8: {mid:.1%}")
    print(f"  > 0.8  : {high:.1%}")
    if low > 0.25 or high > 0.25:
        print("  ⚠ Distribution may be bimodal — consider adjusting generation noise")
    else:
        print("  ✓ Distribution looks healthy")


def evaluate(model, X_test, y_test, feature_cols):
    y_pred = model.predict(X_test)
    y_pred = np.clip(y_pred, 0.0, 1.0)

    mae = mean_absolute_error(y_test, y_pred)
    rmse = mean_squared_error(y_test, y_pred) ** 0.5
    r2 = r2_score(y_test, y_pred)

    print(f"\n── Test Set Metrics ──")
    print(f"  MAE:  {mae:.4f}")
    print(f"  RMSE: {rmse:.4f}")
    print(f"  R²:   {r2:.4f}")

    print(f"\n── Feature Importances ──")
    importances = sorted(
        zip(feature_cols, model.feature_importances_),
        key=lambda x: -x[1]
    )
    for feat, imp in importances:
        label = REASON_LABELS.get(feat, feat)
        bar = "█" * int(imp * 40)
        print(f"  {feat:<28} {imp:.4f}  {bar}  ({label})")

    return mae, r2


def train():
    print("=" * 60)
    print("Option 4 — Student-Opportunity Match Scorer Training")
    print("=" * 60)

    # 1. Load
    df = load_data(DATA_PATH)

    # 2. Add interaction features
    df = add_interaction_features(df)

    # 3. Check score distribution
    check_score_distribution(df["match_score"].values)

    # 4. Build feature matrix
    # Only use columns that exist in the dataset
    available_features = [f for f in FEATURE_COLS if f in df.columns]
    missing = [f for f in FEATURE_COLS if f not in df.columns]
    if missing:
        print(f"\n  Note: computed interaction features added: {[f for f in FEATURE_COLS if f not in df.columns and f in available_features]}")
        print(f"  Missing (will skip): {missing}")

    X = df[available_features].values
    y = df["match_score"].values

    print(f"\nFeatures used ({len(available_features)}): {available_features}")

    # 5. Train/test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    print(f"\nTrain: {X_train.shape[0]} samples | Test: {X_test.shape[0]} samples")

    # 6. Cross-validation
    print("\nRunning 5-fold cross-validation (MAE)...")
    cv_model = GradientBoostingRegressor(
        n_estimators=200, max_depth=4, learning_rate=0.05,
        subsample=0.8, random_state=42
    )
    cv_scores = cross_val_score(cv_model, X_train, y_train, cv=5, scoring="neg_mean_absolute_error")
    cv_mae = -cv_scores
    print(f"  CV MAE scores: {cv_mae.round(4)}")
    print(f"  Mean CV MAE:   {cv_mae.mean():.4f} ± {cv_mae.std():.4f}")

    # 7. Train final model
    print("\nTraining GradientBoostingRegressor...")
    model = GradientBoostingRegressor(
        n_estimators=200,
        max_depth=4,
        learning_rate=0.05,
        subsample=0.8,
        min_samples_leaf=5,
        random_state=42,
    )
    model.fit(X_train, y_train)

    # 8. Evaluate
    mae, r2 = evaluate(model, X_test, y_test, available_features)

    # 9. Save
    joblib.dump(model, SCORER_PATH)
    json.dump(
        {
            "features": available_features,
            "reason_labels": REASON_LABELS,
        },
        open(FEATURES_PATH, "w"),
        indent=2,
    )

    print(f"\n✓ Saved: {SCORER_PATH}")
    print(f"✓ Saved: {FEATURES_PATH}")
    print(f"\nFinal — MAE: {mae:.4f} | R²: {r2:.4f}")
    print("Done.")


if __name__ == "__main__":
    train()
