import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from delta.ml.engine import MLEngine, PredictionResult
from delta.ml.classifier import NaiveBayesClassifier
from delta.ml.anomaly import AnomalyDetector


class MLPipeline:
    def __init__(self, engine: MLEngine):
        self.engine = engine
        self.history: List[Dict[str, Any]] = []

    def auto_train(self, scan_data_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        synthetic = self.engine.generate_synthetic_data(100)
        cls_model = self.engine.train_classifier(synthetic)
        knn_model = self.engine.train_knn(synthetic)
        normal_data = [[0, 0, 0, 0, 0, 0, 1], [1, 0, 0, 1, 0, 0, 2], [2, 1, 0, 1, 0, 0, 2]]
        anomaly_model = self.engine.train_anomaly_detector(normal_data)
        result = {
            "classifier": {"accuracy": f"{cls_model.accuracy:.2%}", "samples": cls_model.samples},
            "knn": {"accuracy": f"{knn_model.accuracy:.2%}", "samples": knn_model.samples},
            "anomaly": {"samples": anomaly_model.samples},
        }
        self.history.append({
            "action": "auto_train",
            "timestamp": datetime.now().isoformat(),
            "result": result,
        })
        return result

    def analyze_scan(self, scan_data: Dict[str, Any]) -> PredictionResult:
        result = self.engine.analyze_scan_data(scan_data)
        anomaly_check = self.engine.detect_anomaly(self.engine._extract_features(scan_data))
        self.history.append({
            "action": "analyze_scan",
            "timestamp": datetime.now().isoformat(),
            "threat": result.label,
            "anomaly": anomaly_check.label,
        })
        return result

    def get_insights(self) -> List[str]:
        insights = []
        for name, status in self.engine.get_status().items():
            insights.append(f"Model '{name}' ({status['type']}): {status['accuracy']} accuracy from {status['samples']} samples")
        if not insights:
            insights.append("No ML models trained yet. Use 'ml train' to begin.")
        return insights

    def export_model_data(self, path: str) -> str:
        data = {
            "models": self.engine.get_status(),
            "history": self.history[-50:],
        }
        os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        return path
