import asyncio
from typing import Dict, Optional
from sentinel.services.news import NewsService
from sentinel.services.llm import LLMService
from sentinel.services.audio import VoiceEngine
from sentinel.interfaces.schemas import RawArticle, NewsScript, FinalPodcast, SpeakerSettings
from sentinel.utils.logger import get_logger

logger = get_logger(__name__)

_FALLBACK_SCORE = 9.5  # Score usado cuando el judge está deshabilitado


class SentinelPipeline:
    def __init__(self):
        self.news_service = NewsService()
        self.llm_service = LLMService()
        self.voice_engine = VoiceEngine()

    async def run_full_process(
        self,
        language: str = "English",
        limit: int = 5,
        voice_mapping: Optional[Dict[str, SpeakerSettings]] = None,
    ) -> FinalPodcast:
        logger.info("Iniciando Sentinel Pipeline [Lang: %s | Limit: %d]", language, limit)

        # 1. Ingesta de Noticias
        articles = await self.news_service.get_top_stories(limit=limit)
        if not articles:
            raise ValueError("No se pudieron obtener noticias de Hacker News.")
        logger.info("Noticias obtenidas: %d artículos", len(articles))

        # 2. Generación del Guion + Judge (Mistral Large 3 + Jinja2)
        script, judge_score = await self.llm_service.generate_dialogue(
            articles=articles,
            language=language,
        )
        logger.info("Script generado: %s", script.headline)

        # 3. Score: real si el judge está activo, fallback si no
        score = judge_score.score if judge_score is not None else _FALLBACK_SCORE
        logger.info("Score final del episodio: %.1f/10", score)

        # 4. Generación del Cover (FLUX.1 via HF)
        cover_path = await self.llm_service.generate_cover(script=script, language=language)

        # 5. Síntesis de Voz (ElevenLabs)
        audio_path = await self.voice_engine.generate_podcast_audio(
            script, voice_mapping=voice_mapping
        )

        logger.info("Pipeline completado. Audio: %s | Cover: %s", audio_path, cover_path)

        # 6. Empaquetado Final
        return FinalPodcast(
            audio_path=audio_path,
            cover_path=cover_path,
            transcript=script,
            language=language,
            score=score,
            sources=articles,
        )


# Ejemplo de ejecución
if __name__ == "__main__":
    pipeline = SentinelPipeline()
    result = asyncio.run(pipeline.run_full_process(language="Spanish"))
    logger.info("Podcast listo en: %s (score: %.1f)", result.audio_path, result.score)