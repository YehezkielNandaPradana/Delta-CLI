"""
ML Engine - Machine learning models for threat prediction and anomaly detection.
Provides offline classification, anomaly detection, and model management.
"""

import json
import os
import math
import random
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field

from delta.ml.classifier import NaiveBayesClassifier, KNNClassifier
from delta.ml.anomaly import AnomalyDetector


@dataclass
class MLModel:
    name: str
    model_type: str
    accuracy: float = 0.0
    trained_at: str = ""
    samples: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PredictionResult:
    label: str
    confidence: float
    probabilities: Dict[str, float] = field(default_factory=dict)
    explanation: str = ""


class MLEngine:
    def __init__(self, data_dir: str = ""):
        self.data_dir = data_dir
        self.models: Dict[str, MLModel] = {}
        self._classifier: Optional[NaiveBayesClassifier] = None
        self._knn: Optional[KNNClassifier] = None
        self._anomaly: Optional[AnomalyDetector] = None
        self._load_models()

    def _load_models(self) -> None:
        if not self.data_dir:
            return
        models_path = os.path.join(self.data_dir, "ml_models.json")
        if os.path.exists(models_path):
            try:
                with open(models_path) as f:
                    data = json.load(f)
                    for name, info in data.items():
                        self.models[name] = MLModel(**info)
            except Exception:
                pass

    def _save_models(self) -> None:
        if not self.data_dir:
            return
        models_path = os.path.join(self.data_dir, "ml_models.json")
        os.makedirs(os.path.dirname(models_path), exist_ok=True)
        data = {name: {
            "name": m.name, "model_type": m.model_type,
            "accuracy": m.accuracy, "trained_at": m.trained_at,
            "samples": m.samples, "metadata": m.metadata,
        } for name, m in self.models.items()}
        with open(models_path, "w") as f:
            json.dump(data, f, indent=2)

    def train_classifier(self, samples: List[Tuple[List[float], str]]) -> MLModel:
        self._classifier = NaiveBayesClassifier()
        self._classifier.train(samples)
        accuracy = self._classifier.evaluate(samples)
        model = MLModel(
            name="threat_classifier",
            model_type="naive_bayes",
            accuracy=accuracy,
            trained_at=datetime.now().isoformat(),
            samples=len(samples),
        )
        self.models["threat_classifier"] = model
        self._save_models()
        return model

    def train_knn(self, samples: List[Tuple[List[float], str]], k: int = 3) -> MLModel:
        self._knn = KNNClassifier(k=k)
        self._knn.train(samples)
        accuracy = self._knn.evaluate(samples)
        model = MLModel(
            name="pattern_recognizer",
            model_type="knn",
            accuracy=accuracy,
            trained_at=datetime.now().isoformat(),
            samples=len(samples),
        )
        self.models["pattern_recognizer"] = model
        self._save_models()
        return model

    def train_anomaly_detector(self, data: List[List[float]], threshold: float = 2.0) -> MLModel:
        self._anomaly = AnomalyDetector(threshold=threshold)
        self._anomaly.train(data)
        model = MLModel(
            name="anomaly_detector",
            model_type="gaussian_anomaly",
            accuracy=1.0,
            trained_at=datetime.now().isoformat(),
            samples=len(data),
        )
        self.models["anomaly_detector"] = model
        self._save_models()
        return model

    def predict_threat(self, features: List[float]) -> PredictionResult:
        if not self._classifier:
            return PredictionResult(
                label="unknown",
                confidence=0.0,
                explanation="No trained classifier. Use 'ml train' first."
            )
        label, confidence, probs = self._classifier.predict(features)
        return PredictionResult(
            label=label,
            confidence=confidence,
            probabilities=probs,
            explanation=self._explain_threat(label, confidence),
        )

    def predict_pattern(self, features: List[float]) -> PredictionResult:
        if not self._knn:
            return PredictionResult(
                label="unknown",
                confidence=0.0,
                explanation="No trained KNN model. Use 'ml train' first."
            )
        label, confidence, probs = self._knn.predict(features)
        return PredictionResult(
            label=label,
            confidence=confidence,
            probabilities=probs,
            explanation=f"Pattern matched: {label} with {confidence:.1%} confidence",
        )

    def detect_anomaly(self, data_point: List[float]) -> PredictionResult:
        if not self._anomaly:
            return PredictionResult(
                label="unknown",
                confidence=0.0,
                explanation="No trained anomaly detector. Use 'ml train' first."
            )
        is_anomaly, score = self._anomaly.predict(data_point)
        label = "anomaly" if is_anomaly else "normal"
        confidence = min(abs(score), 1.0)
        return PredictionResult(
            label=label,
            confidence=confidence,
            explanation=f"Anomaly score: {score:.4f} (threshold: {self._anomaly.threshold})",
        )

    def _explain_threat(self, label: str, confidence: float) -> str:
        explanations = {
            "critical": "Immediate attention required. Multiple high-risk indicators detected.",
            "high": "Significant security risk detected. Investigate and remediate promptly.",
            "medium": "Moderate risk level. Review and address findings.",
            "low": "Minor security concerns. Address during next maintenance cycle.",
            "safe": "No significant threats detected. Continue monitoring.",
        }
        base = explanations.get(label, f"Classification: {label}")
        return f"{base} (confidence: {confidence:.1%})"

    def analyze_scan_data(self, scan_data: Dict[str, Any]) -> PredictionResult:
        features = self._extract_features(scan_data)
        if not features:
            return PredictionResult(label="no_data", confidence=0.0, explanation="Insufficient scan data for ML analysis")
        return self.predict_threat(features)

    def _extract_features(self, scan_data: Dict[str, Any]) -> List[float]:
        features = []
        ports = scan_data.get("open_ports", [])
        features.append(len(ports))
        dangerous = sum(1 for p in ports if isinstance(p, dict) and p.get("port", 0) in (21, 23, 25, 445, 1433, 3306, 3389))
        features.append(dangerous)
        vulns = scan_data.get("vulnerabilities", [])
        features.append(len(vulns))
        headers = scan_data.get("headers", {})
        missing_headers = sum(1 for h in ["strict-transport-security", "x-frame-options", "x-content-type-options", "content-security-policy"] if h not in {k.lower(): v for k, v in headers.items()})
        features.append(missing_headers)
        ssl = scan_data.get("ssl", {})
        features.append(1 if ssl.get("expired") else 0)
        features.append(1 if ssl.get("self_signed") else 0)
        features.append(len(scan_data.get("services", {})))
        return features

    def get_status(self) -> Dict[str, Any]:
        status = {}
        for name, model in self.models.items():
            status[name] = {
                "type": model.model_type,
                "accuracy": f"{model.accuracy:.2%}",
                "samples": model.samples,
                "trained": model.trained_at[:19] if model.trained_at else "never",
            }
        return status

    def generate_synthetic_data(self, num_samples: int = 50) -> List[Tuple[List[float], str]]:
        samples = []
        for _ in range(num_samples):
            base_type = random.choice(["safe", "low", "medium", "high", "critical"])
            if base_type == "safe":
                features = [random.randint(0, 3), 0, 0, random.randint(0, 1), 0, 0, random.randint(0, 2)]
            elif base_type == "low":
                features = [random.randint(2, 6), random.randint(0, 1), random.randint(0, 1), random.randint(1, 2), 0, 0, random.randint(1, 3)]
            elif base_type == "medium":
                features = [random.randint(5, 10), random.randint(1, 3), random.randint(1, 3), random.randint(2, 3), random.randint(0, 1), random.randint(0, 1), random.randint(2, 5)]
            elif base_type == "high":
                features = [random.randint(8, 15), random.randint(2, 5), random.randint(2, 5), random.randint(3, 4), random.randint(0, 1), random.randint(0, 1), random.randint(3, 6)]
            else:
                features = [random.randint(12, 20), random.randint(3, 8), random.randint(4, 8), random.randint(4, 5), 1, random.randint(0, 1), random.randint(4, 8)]
            samples.append((features, base_type))
        return samples
