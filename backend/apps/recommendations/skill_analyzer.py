from transformers import pipeline
from django.conf import settings
import os

class SkillAnalyzer:
    def __init__(self):
        # Загрузка модели для анализа текста
        model_path = os.getenv('MODEL_PATH', 'distilbert-base-uncased-finetuned-sst-2-english')
        self.classifier = pipeline(
            "text-classification",
            model=model_path,
            device=-1 if not settings.USE_CUDA else 0
        )

    def analyze_description(self, description: str) -> dict:
        """Анализирует описание навыка"""
        result = self.classifier(description[:512])[0]

        # Простая логика определения уровня
        score = result["score"]
        if score > 0.8:
            level = "advanced"
        elif score > 0.5:
            level = "intermediate"
        else:
            level = "beginner"

        return {
            "level": level,
            "confidence": score,
            "labels": result["label"]
        }
