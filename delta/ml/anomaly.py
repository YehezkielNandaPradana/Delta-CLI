import math
from typing import List, Tuple


class AnomalyDetector:
    def __init__(self, threshold: float = 2.0):
        self.threshold = threshold
        self.means: List[float] = []
        self.stds: List[float] = []
        self.trained = False

    def train(self, data: List[List[float]]) -> None:
        if not data:
            return
        n_features = len(data[0])
        self.means = []
        self.stds = []
        for i in range(n_features):
            vals = [d[i] for d in data]
            mean = sum(vals) / len(vals)
            variance = sum((v - mean) ** 2 for v in vals) / len(vals)
            std = math.sqrt(variance + 1e-9)
            self.means.append(mean)
            self.stds.append(std)
        self.trained = True

    def _mahalanobis_distance(self, point: List[float]) -> float:
        if not self.trained:
            return 0.0
        dist = 0.0
        for i, val in enumerate(point):
            if i < len(self.means) and self.stds[i] > 0:
                dist += ((val - self.means[i]) / self.stds[i]) ** 2
        return math.sqrt(dist)

    def predict(self, point: List[float]) -> Tuple[bool, float]:
        if not self.trained:
            return False, 0.0
        distance = self._mahalanobis_distance(point)
        is_anomaly = distance > self.threshold
        return is_anomaly, distance
