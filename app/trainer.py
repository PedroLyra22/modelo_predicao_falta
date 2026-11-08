import os
import datetime
import numpy as np
import pandas as pd
import joblib
from typing import Dict, Any, Tuple
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor, HistGradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

FEATURES = [
    "Jogos Futebol", "Clima", "Choveu?", "Dia da Semana",
    "Feriado (antes)", "Feriado (depois)", "Trânsito", "TURNO"
]

NUMERIC_FEATURES = ["Jogos Futebol", "Choveu?", "Feriado (antes)", "Feriado (depois)", "Trânsito"]
CATEGORICAL_FEATURES = ["Clima", "Dia da Semana", "TURNO"]
TARGET_COL = "%"

def build_preprocessor() -> ColumnTransformer:
    return ColumnTransformer([
        ("num", SimpleImputer(strategy="median"), NUMERIC_FEATURES),
        ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), CATEGORICAL_FEATURES)
    ])

def extract_feature_importances(pipeline: Pipeline) -> Dict[str, Any]:
    """
    Extrai a importância/pesos das features do modelo treinado.
    Agrupa por variável original e detalha por categoria dummificada.
    """
    try:
        prep = pipeline.named_steps["prep"]
        model = pipeline.named_steps["model"]

        num_cols = NUMERIC_FEATURES
        cat_encoder = prep.named_transformers_["cat"]
        cat_cols = cat_encoder.get_feature_names_out(CATEGORICAL_FEATURES).tolist()
        transformed_names = num_cols + cat_cols

        raw_weights = None
        if hasattr(model, "feature_importances_"):
            raw_weights = model.feature_importances_
        elif hasattr(model, "coef_"):
            coefs = np.abs(model.coef_)
            total = coefs.sum() if coefs.sum() > 0 else 1.0
            raw_weights = coefs / total

        if raw_weights is None:
            raw_weights = [1.0 / len(transformed_names)] * len(transformed_names)

        detailed_weights = []
        grouped_weights: Dict[str, float] = {col: 0.0 for col in FEATURES}

        for name, weight in zip(transformed_names, raw_weights):
            val_pct = round(float(weight) * 100, 2)
            detailed_weights.append({
                "feature": name,
                "weight_pct": val_pct
            })

            matched = False
            for original in FEATURES:
                if original in name:
                    grouped_weights[original] += float(weight)
                    matched = True
                    break
            if not matched:
                grouped_weights["Outros"] = grouped_weights.get("Outros", 0.0) + float(weight)

        grouped_list = [
            {"feature": k, "weight_pct": round(v * 100, 2)}
            for k, v in sorted(grouped_weights.items(), key=lambda x: x[1], reverse=True)
        ]

        detailed_weights.sort(key=lambda x: x["weight_pct"], reverse=True)

        return {
            "grouped": grouped_list,
            "detailed": detailed_weights
        }
    except Exception as e:
        print(f"Erro ao extrair importâncias: {e}")
        return {
            "grouped": [{"feature": f, "weight_pct": round(100.0 / len(FEATURES), 2)} for f in FEATURES],
            "detailed": []
        }

def train_and_evaluate_models(
    csv_path: str,
    output_dir: str,
    version_tag: str,
    test_size: float = 0.2
) -> Dict[str, Any]:
    """
    Treina múltiplos modelos de regressão, compara desempenhos e salva a versão escolhida.
    Permite customizar a proporção de divisão treino/teste (padrão: 80% treino / 20% teste).
    """
    try:
        test_size = float(test_size)
        if test_size <= 0.0 or test_size >= 1.0:
            test_size = 0.2
    except (ValueError, TypeError):
        test_size = 0.2

    df = pd.read_csv(csv_path)

    missing_cols = [c for c in FEATURES if c not in df.columns]
    if missing_cols:
        raise ValueError(f"O CSV não possui as colunas obrigatórias: {missing_cols}")

    if TARGET_COL not in df.columns:
        alt_targets = [c for c in df.columns if "%" in c or "falta" in c.lower()]
        if alt_targets:
            target_to_use = alt_targets[0]
        else:
            raise ValueError(f"Coluna alvo '{TARGET_COL}' não encontrada no CSV.")
    else:
        target_to_use = TARGET_COL

    df = df.dropna(subset=[target_to_use])
    df = df[df[target_to_use] >= 0]
    total_samples = len(df)

    if total_samples < 20:
        raise ValueError("O dataset deve conter pelo menos 20 linhas para treino e validação.")

    X = df[FEATURES].copy()
    y = df[target_to_use].astype(float)

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=42)

    candidate_models = {
        "RandomForest": RandomForestRegressor(n_estimators=300, random_state=42, n_jobs=-1),
        "GradientBoosting": GradientBoostingRegressor(random_state=42),
        "Ridge": Ridge(alpha=1.0),
        "HistGradientBoosting": HistGradientBoostingRegressor(random_state=42)
    }

    results = {}
    best_name = None
    best_mae = float("inf")
    best_pipeline = None

    for name, regressor in candidate_models.items():
        pipe = Pipeline([
            ("prep", build_preprocessor()),
            ("model", regressor)
        ])
        pipe.fit(X_train, y_train)
        preds = pipe.predict(X_test)

        mae = float(mean_absolute_error(y_test, preds))
        rmse = float(np.sqrt(mean_squared_error(y_test, preds)))
        r2 = float(r2_score(y_test, preds))

        results[name] = {
            "MAE": round(mae, 3),
            "RMSE": round(rmse, 3),
            "R2": round(r2, 3)
        }

        if mae < best_mae:
            best_mae = mae
            best_name = name
            best_pipeline = pipe

    os.makedirs(output_dir, exist_ok=True)
    filename = f"modelo_{version_tag}.joblib"
    saved_path = os.path.join(output_dir, filename)
    joblib.dump(best_pipeline, saved_path)

    weights_info = extract_feature_importances(best_pipeline)

    train_pct = int(round((1.0 - test_size) * 100))
    test_pct = int(round(test_size * 100))

    summary = {
        "version": version_tag,
        "filename": filename,
        "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "best_algorithm": best_name,
        "best_metrics": results[best_name],
        "all_algorithms_comparison": results,
        "total_samples": total_samples,
        "test_size": test_size,
        "train_ratio_pct": train_pct,
        "test_ratio_pct": test_pct,
        "split_label": f"{train_pct}% Treino / {test_pct}% Teste",
        "train_samples": len(X_train),
        "test_samples": len(X_test),
        "target_mean": round(float(y.mean()), 2),
        "target_min": round(float(y.min()), 2),
        "target_max": round(float(y.max()), 2),
        "weights": weights_info
    }

    return summary
