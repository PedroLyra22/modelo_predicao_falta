import os
import json
import shutil
import pandas as pd
import joblib
from typing import Dict, Any, List, Optional
from app.app import FEATURES, extract_feature_importances

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR = os.path.join(BASE_DIR, "models")
REGISTRY_PATH = os.path.join(MODELS_DIR, "registry.json")

class ModelService:
    def __init__(self):
        os.makedirs(MODELS_DIR, exist_ok=True)
        self.cached_models: Dict[str, Any] = {}
        self._ensure_initial_registry()

    def _ensure_initial_registry(self):
        """Inicializa o registro se não existir ou se estiver vazio."""
        if not os.path.exists(REGISTRY_PATH):
            initial_data = {
                "active_version": "v1.0-default",
                "models": []
            }
            # Se já existir o modelo de 1500 linhas na raiz ou na pasta models, inclui no registro
            source_model_1500 = os.path.join(BASE_DIR, "modelo_falta_escola_1500.joblib")
            dest_model_1500 = os.path.join(MODELS_DIR, "modelo_falta_escola_1500.joblib")

            if os.path.exists(source_model_1500) and not os.path.exists(dest_model_1500):
                shutil.copy2(source_model_1500, dest_model_1500)

            if os.path.exists(dest_model_1500):
                try:
                    loaded = joblib.load(dest_model_1500)
                    weights = extract_feature_importances(loaded)
                except Exception:
                    weights = {"grouped": [], "detailed": []}

                initial_data["models"].append({
                    "version": "v1.0-default",
                    "filename": "modelo_falta_escola_1500.joblib",
                    "created_at": "2026-10-31 12:00:00",
                    "description": "Modelo inicial treinado na base de 1.500 registros de São Paulo",
                    "best_algorithm": "RandomForest",
                    "best_metrics": {"MAE": 2.15, "RMSE": 3.02, "R2": 0.68},
                    "total_samples": 1500,
                    "target_mean": 12.36,
                    "weights": weights
                })
            
            with open(REGISTRY_PATH, "w", encoding="utf-8") as f:
                json.dump(initial_data, f, indent=2, ensure_ascii=False)

    def get_registry(self) -> Dict[str, Any]:
        if not os.path.exists(REGISTRY_PATH):
            self._ensure_initial_registry()
        try:
            with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"active_version": None, "models": []}

    def save_registry(self, data: Dict[str, Any]):
        with open(REGISTRY_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def list_models(self) -> List[Dict[str, Any]]:
        reg = self.get_registry()
        active = reg.get("active_version")
        models = reg.get("models", [])
        for m in models:
            m["is_active"] = (m.get("version") == active)
        return models

    def get_active_model_info(self) -> Optional[Dict[str, Any]]:
        reg = self.get_registry()
        active = reg.get("active_version")
        for m in reg.get("models", []):
            if m.get("version") == active:
                m["is_active"] = True
                return m
        # Se nenhum ativo for achado, pega o primeiro
        models = reg.get("models", [])
        if models:
            models[0]["is_active"] = True
            return models[0]
        return None

    def set_active_version(self, version_tag: str) -> bool:
        reg = self.get_registry()
        found = any(m.get("version") == version_tag for m in reg.get("models", []))
        if not found:
            return False
        reg["active_version"] = version_tag
        self.save_registry(reg)
        return True

    def register_new_model(self, summary: Dict[str, Any], set_active: bool = True):
        reg = self.get_registry()
        # Remove versão antiga de mesmo nome se houver
        models = [m for m in reg.get("models", []) if m.get("version") != summary["version"]]
        models.insert(0, summary)
        reg["models"] = models
        if set_active:
            reg["active_version"] = summary["version"]
        self.save_registry(reg)

    def load_pipeline(self, version_tag: Optional[str] = None):
        reg = self.get_registry()
        if not version_tag:
            version_tag = reg.get("active_version")

        # Busca metadados da versão
        model_meta = None
        for m in reg.get("models", []):
            if m.get("version") == version_tag:
                model_meta = m
                break

        if not model_meta:
            raise FileNotFoundError(f"Versão de modelo '{version_tag}' não encontrada no registro.")

        filename = model_meta.get("filename")
        model_path = os.path.join(MODELS_DIR, filename)

        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Arquivo de modelo '{filename}' não encontrado em disco.")

        if version_tag not in self.cached_models:
            self.cached_models[version_tag] = joblib.load(model_path)

        return self.cached_models[version_tag], model_meta

    def predict_absence(
        self,
        payload: Dict[str, Any],
        version_tag: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executa a predição da porcentagem de falta escolar.
        """
        pipeline, meta = self.load_pipeline(version_tag)

        # Monta DataFrame com as colunas esperadas
        row = {
            "Jogos Futebol": int(payload.get("jogos_futebol", 0)),
            "Clima": str(payload.get("clima", "Ensolarado")),
            "Choveu?": int(payload.get("choveu", 0)),
            "Dia da Semana": str(payload.get("dia_da_semana", "Quarta")),
            "Feriado (antes)": int(payload.get("feriado_antes", 0)),
            "Feriado (depois)": int(payload.get("feriado_depois", 0)),
            "Trânsito": int(payload.get("transito", 3)),
            "TURNO": str(payload.get("turno", "Manhã"))
        }

        df_input = pd.DataFrame([row])[FEATURES]
        pred_val = float(pipeline.predict(df_input)[0])
        # Garante limites lógicos [0%, 100%]
        pred_val = max(0.0, min(100.0, pred_val))
        pred_val = round(pred_val, 2)

        # Classificação de Risco
        if pred_val < 10.0:
            risk_level = "Baixo"
            risk_color = "#10b981"  # Verde esmeralda
            risk_badge = "success"
            risk_message = "Ausência dentro do esperado. Rotina escolar regular e estável."
        elif pred_val <= 18.0:
            risk_level = "Moderado"
            risk_color = "#f59e0b"  # Amarelo/Âmbar
            risk_badge = "warning"
            risk_message = "Atenção recomendada: fatores ambientais ou do calendário elevam a probabilidade de faltas."
        else:
            risk_level = "Crítico / Alto"
            risk_color = "#ef4444"  # Vermelho
            risk_badge = "danger"
            risk_message = "Alerta de alto absenteísmo! Forte influência de clima adverso, feriados ou trânsito."

        # Projeções práticas de impacto escolar
        sala_40 = round((pred_val / 100.0) * 40)
        escola_500 = round((pred_val / 100.0) * 500)
        escola_1000 = round((pred_val / 100.0) * 1000)

        # Comparação com média histórica
        historical_mean = meta.get("target_mean", 12.36)
        diff_mean = round(pred_val - historical_mean, 2)

        # Fatores de destaque no input
        factors = []
        if row["Choveu?"] == 1 or row["Clima"] == "Chuvoso":
            factors.append({"name": "Chuva / Clima Chuvoso", "impact": "Aumenta absenteísmo (+)"})
        if row["Feriado (antes)"] == 1:
            factors.append({"name": "Véspera de Feriado", "impact": "Propensão à ausência (+)"})
        if row["Feriado (depois)"] == 1:
            factors.append({"name": "Pós-Feriado (Emenda)", "impact": "Propensão à ausência (+)"})
        if row["Trânsito"] >= 4:
            factors.append({"name": "Trânsito Intenso/Caótico", "impact": "Atrasos e desistências (+)"})
        if row["Jogos Futebol"] == 1:
            factors.append({"name": "Dia de Futebol/Evento", "impact": "Distração de público (+)"})
        if not factors:
            factors.append({"name": "Dia Típico Regular", "impact": "Condições favoráveis de presença (=)"})

        return {
            "prediction_pct": pred_val,
            "risk_level": risk_level,
            "risk_color": risk_color,
            "risk_badge": risk_badge,
            "risk_message": risk_message,
            "projections": {
                "turma_40_alunos": sala_40,
                "escola_500_alunos": escola_500,
                "escola_1000_alunos": escola_1000
            },
            "historical_mean": historical_mean,
            "difference_from_mean": diff_mean,
            "key_factors": factors,
            "inputs": row,
            "model_used": {
                "version": meta.get("version"),
                "algorithm": meta.get("best_algorithm", "Machine Learning"),
                "mae": meta.get("best_metrics", {}).get("MAE")
            }
        }
