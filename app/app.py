import os
import datetime
from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
from app.model_service import ModelService, BASE_DIR, MODELS_DIR
from app.trainer import train_and_evaluate_models, extract_feature_importances
from app.open_data_service import get_complete_open_data

app = Flask(__name__)
app.config["SECRET_KEY"] = "tcc-predicao-faltas-secret-key-2026"
app.config["MAX_CONTENT_LENGTH"] = 32 * 1024 * 1024  # 32MB max
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

model_service = ModelService()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy", "service": "TCC Predição de Faltas Escolares API"})

@app.route("/api/predict", methods=["POST"])
def predict():
    try:
        data = request.get_json(force=True)
        version = data.get("version")
        result = model_service.predict_absence(data, version_tag=version)
        return jsonify({"success": True, "data": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@app.route("/api/weights", methods=["GET"])
def get_weights():
    try:
        version = request.args.get("version")
        pipeline, meta = model_service.load_pipeline(version)
        weights = meta.get("weights")
        if not weights or not weights.get("grouped"):
            weights = extract_feature_importances(pipeline)
            meta["weights"] = weights
            # Atualiza no registro
            reg = model_service.get_registry()
            for m in reg.get("models", []):
                if m.get("version") == meta.get("version"):
                    m["weights"] = weights
            model_service.save_registry(reg)

        return jsonify({
            "success": True,
            "version": meta.get("version"),
            "algorithm": meta.get("best_algorithm"),
            "metrics": meta.get("best_metrics"),
            "weights": weights,
            "total_samples": meta.get("total_samples"),
            "target_mean": meta.get("target_mean")
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@app.route("/api/models", methods=["GET"])
def list_models():
    try:
        models = model_service.list_models()
        return jsonify({"success": True, "models": models})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/models/activate", methods=["POST"])
def activate_model():
    try:
        data = request.get_json(force=True)
        version = data.get("version")
        if not version:
            return jsonify({"success": False, "error": "Versão não especificada."}), 400
        success = model_service.set_active_version(version)
        if success:
            return jsonify({"success": True, "message": f"Versão '{version}' ativada com sucesso."})
        return jsonify({"success": False, "error": f"Versão '{version}' não encontrada."}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/default-datasets", methods=["GET"])
def list_default_datasets():
    """Lista bases CSV disponíveis no repositório para treino facilitado."""
    csv_files = []
    for f in os.listdir(BASE_DIR):
        if f.endswith(".csv"):
            fpath = os.path.join(BASE_DIR, f)
            size_kb = round(os.path.getsize(fpath) / 1024, 1)
            csv_files.append({
                "filename": f,
                "size_kb": size_kb
            })
    return jsonify({"success": True, "datasets": csv_files})

@app.route("/api/train", methods=["POST"])
def train():
    try:
        version_name = request.form.get("version_name", "").strip()
        use_default = request.form.get("default_dataset", "").strip()
        set_active = request.form.get("set_active", "true").lower() == "true"
        test_size_raw = request.form.get("test_size", "0.2").strip()
        try:
            test_size = float(test_size_raw)
            if test_size <= 0.0 or test_size >= 1.0:
                test_size = 0.2
        except (ValueError, TypeError):
            test_size = 0.2

        if not version_name:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            version_name = f"v_{timestamp}"

        # Trata o arquivo: ou upload ou dataset padrão
        csv_path = None
        if "file" in request.files and request.files["file"].filename != "":
            file = request.files["file"]
            filename = secure_filename(file.filename)
            csv_path = os.path.join(app.config["UPLOAD_FOLDER"], f"{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}")
            file.save(csv_path)
        elif use_default:
            default_path = os.path.join(BASE_DIR, secure_filename(use_default))
            if os.path.exists(default_path):
                csv_path = default_path
            else:
                return jsonify({"success": False, "error": "Dataset padrão especificado não existe."}), 400
        else:
            return jsonify({"success": False, "error": "Nenhum arquivo CSV enviado e nenhum dataset padrão selecionado."}), 400

        # Treina e avalia modelos
        summary = train_and_evaluate_models(
            csv_path=csv_path,
            output_dir=MODELS_DIR,
            version_tag=version_name,
            test_size=test_size
        )

        # Registra a nova versão
        model_service.register_new_model(summary, set_active=set_active)

        return jsonify({
            "success": True,
            "message": f"Modelo treinado e versionado com sucesso como '{version_name}'!",
            "summary": summary
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@app.route("/api/open-data", methods=["GET"])
def get_open_data():
    """
    Consulta dados em tempo real ou históricos via 5 APIs abertas:
    Open-Meteo Weather, BrasilAPI, ESPN Futebol, Open-Meteo Air Quality e Nominatim.
    """
    try:
        date_str = request.args.get("date")
        location_query = request.args.get("location", "").strip()
        turno = request.args.get("turno", "Manhã")
        lat = request.args.get("lat")
        lon = request.args.get("lon")

        lat_val = float(lat) if lat else None
        lon_val = float(lon) if lon else None

        data = get_complete_open_data(
            date_str=date_str,
            location_query=location_query if location_query else None,
            lat=lat_val,
            lon=lon_val,
            turno=turno
        )
        return jsonify({"success": True, "data": data})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
