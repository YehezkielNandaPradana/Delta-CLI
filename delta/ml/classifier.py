import math
from typing import Any, Dict, List, Optional, Tuple


class NaiveBayesClassifier:
    def __init__(self):
        self.classes: List[str] = []
        self.class_priors: Dict[str, float] = {}
        self.means: Dict[str, List[float]] = {}
        self.stds: Dict[str, List[float]] = {}
        self.trained = False

    def train(self, samples: List[Tuple[List[float], str]]) -> None:
        if not samples:
            return
        class_groups: Dict[str, List[List[float]]] = {}
        for features, label in samples:
            if label not in class_groups:
                class_groups[label] = []
            class_groups[label].append(features)
        self.classes = list(class_groups.keys())
        total = len(samples)
        for cls, feats_list in class_groups.items():
            self.class_priors[cls] = len(feats_list) / total
            n_features = len(feats_list[0])
            means = []
            stds = []
            for i in range(n_features):
                vals = [f[i] for f in feats_list]
                mean = sum(vals) / len(vals)
                variance = sum((v - mean) ** 2 for v in vals) / len(vals)
                std = math.sqrt(variance + 1e-9)
                means.append(mean)
                stds.append(std)
            self.means[cls] = means
            self.stds[cls] = stds
        self.trained = True

    def _gaussian_prob(self, x: float, mean: float, std: float) -> float:
        exponent = -((x - mean) ** 2) / (2 * std ** 2)
        return (1.0 / (math.sqrt(2 * math.pi) * std)) * math.exp(exponent)

    def predict(self, features: List[float]) -> Tuple[str, float, Dict[str, float]]:
        if not self.trained:
            return "unknown", 0.0, {}
        posteriors: Dict[str, float] = {}
        for cls in self.classes:
            log_prob = math.log(self.class_priors.get(cls, 1e-9))
            for i, feat in enumerate(features):
                if i < len(self.means.get(cls, [])):
                    prob = self._gaussian_prob(feat, self.means[cls][i], self.stds[cls][i])
                    log_prob += math.log(max(prob, 1e-300))
            posteriors[cls] = log_prob
        total_exp = sum(math.exp(p) for p in posteriors.values())
        probs = {cls: math.exp(p) / total_exp for cls, p in posteriors.items()}
        best_cls = max(posteriors, key=posteriors.get)
        confidence = probs[best_cls]
        return best_cls, confidence, probs

    def evaluate(self, samples: List[Tuple[List[float], str]]) -> float:
        if not samples:
            return 0.0
        correct = 0
        for features, label in samples:
            predicted, _, _ = self.predict(features)
            if predicted == label:
                correct += 1
        return correct / len(samples)


class KNNClassifier:
    def __init__(self, k: int = 3):
        self.k = k
        self.samples: List[Tuple[List[float], str]] = []

    def train(self, samples: List[Tuple[List[float], str]]) -> None:
        self.samples = samples

    def _euclidean(self, a: List[float], b: List[float]) -> float:
        return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))

    def predict(self, features: List[float]) -> Tuple[str, float, Dict[str, float]]:
        if not self.samples:
            return "unknown", 0.0, {}
        distances = [(self._euclidean(features, s[0]), s[1]) for s in self.samples]
        distances.sort(key=lambda x: x[0])
        neighbors = distances[:self.k]
        votes: Dict[str, int] = {}
        for _, label in neighbors:
            votes[label] = votes.get(label, 0) + 1
        total = sum(votes.values())
        probs = {cls: count / total for cls, count in votes.items()}
        best_cls = max(votes, key=votes.get)
        confidence = probs[best_cls]
        return best_cls, confidence, probs

    def evaluate(self, samples: List[Tuple[List[float], str]]) -> float:
        if not samples:
            return 0.0
        correct = 0
        for features, label in samples:
            predicted, _, _ = self.predict(features)
            if predicted == label:
                correct += 1
        return correct / len(samples)
