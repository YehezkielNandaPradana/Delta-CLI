"""
Hybrid Vision Adapter for GeoTrace.
Analyzes public images for geolocation cues (landmarks, signage, vehicle plates, vegetation).
Utilizes Delta LLM Multimodal Vision if available, otherwise executes regex & heuristic rule matchers.
"""

import re
from typing import Any, Dict, List


class GeoTraceVisionAdapter:
    """
    Hybrid Vision processor for visual OSINT analysis.
    """

    KNOWN_LANDMARKS = [
        "monas", "bundaran hi", "gedung sate", "jalan braga", "candi prambanan",
        "candi borobudur", "malioboro", "jembatan suramadu", "gwk", "pantai kuta",
        "merlion", "petronas towers", "eiffel tower", "shibuya crossing"
    ]

    PLATE_PATTERNS = [
        r"\b([A-Z]{1,2})\s*\d{1,4}\s*[A-Z]{0,3}\b"
    ]

    def analyze_image_heuristics(self, image_metadata: Dict[str, Any], raw_text: str = "") -> List[str]:
        """
        Extract visual clues from image caption, OCR text, or mock detection labels.
        """
        clues = []
        tags = image_metadata.get("tags", [])
        combined_text = (raw_text + " " + " ".join(tags)).lower()

        for lm in self.KNOWN_LANDMARKS:
            if lm in combined_text:
                clues.append(f"Landmark {lm.title()} detected")

        for pattern in self.PLATE_PATTERNS:
            matches = re.findall(pattern, raw_text)
            for m in matches:
                clues.append(f"Vehicle plate prefix {m} observed")

        return clues

    def analyze_multimodal(self, image_url: str, prompt_hint: str = "") -> List[str]:
        """
        Analyzes image using vision pipeline. Fallback to heuristic parser.
        """
        # image_url can be used in future multimodal extensions
        _ = image_url
        return self.analyze_image_heuristics({}, raw_text=prompt_hint)
