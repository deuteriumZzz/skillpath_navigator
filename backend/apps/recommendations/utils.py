from transformers import pipeline
from django.conf import settings
import os

class SkillLevelAnalyzer:
    def __init__(self):
        model_path = "distilbert-base-uncased-finetuned-sst-2-english"
        self.classifier = pipeline(
            "text-classification",
            model=model_path,
            device=-1 if not settings.USE_CUDA else 0
        )

    def analyze(self, text):
        result = self.classifier(text[:512])[0]
        score = result["score"]

        if score > 0.7:
            return "advanced"
        elif score > 0.4:
            return "intermediate"
        else:
            return "beginner"
