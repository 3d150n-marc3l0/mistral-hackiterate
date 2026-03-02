import os
from PIL import Image
import io
import tempfile
from typing import List, Optional, Tuple
from mistralai import Mistral
from jinja2 import Environment, FileSystemLoader
from huggingface_hub import InferenceClient

import sentinel.utils.config  # noqa: F401 – carga el .env al importar
from sentinel.interfaces.schemas import RawArticle, NewsScript, JudgeScore
from sentinel.utils.logger import get_logger

logger = get_logger(__name__)


class LLMService:
    def __init__(self):
        self.mistral_client = Mistral(api_key=os.getenv("MISTRAL_API_KEY"))
        self.hf_client = InferenceClient(
            provider=os.getenv("HF_IMAGE_PROVIDER", "together"),
            token=os.getenv("HF_API_KEY"),
        )
        self.jinja_env = Environment(loader=FileSystemLoader("src/sentinel/prompts"))

        # Configuración del judge
        self._judge_enabled = os.getenv("JUDGE_ENABLED", "false").lower() == "true"
        self._judge_model = os.getenv("JUDGE_MODEL", "mistral-small-latest")

        if self._judge_enabled:
            logger.info("LLM-Judge habilitado con modelo: %s", self._judge_model)
        else:
            logger.info("LLM-Judge deshabilitado (JUDGE_ENABLED != true)")

    # ──────────────────────────────────────────────────────────────────────────
    # Generación del guion
    # ──────────────────────────────────────────────────────────────────────────

    async def generate_dialogue(
        self,
        articles: List[RawArticle],
        language: str = "English",
    ) -> Tuple[NewsScript, Optional[JudgeScore]]:
        """Genera el guion del podcast y, opcionalmente, lo evalúa con el judge.

        Returns:
            (NewsScript, JudgeScore | None)
        """
        # 1. Renderizar prompt y llamar a Mistral
        template = self.jinja_env.get_template("podcast_script.jinja2")
        prompt = template.render(articles=articles, language=language, duration_seconds=120)
        logger.debug("Script Podcast Prompt:\n%s", prompt)

        response = await self.mistral_client.chat.complete_async(
            model="mistral-large-latest",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
        )
        script = NewsScript.model_validate_json(response.choices[0].message.content)
        logger.info("Script generado: %s (%d líneas de diálogo)", script.headline, len(script.dialogue))

        # 2. Judge (opcional)
        judge_score: Optional[JudgeScore] = None
        if self._judge_enabled:
            try:
                judge_score = await self.judge_dialogue(script, articles, language)
            except Exception:
                logger.exception("Error en el LLM-Judge; se continúa sin score.")

        return script, judge_score

    # ──────────────────────────────────────────────────────────────────────────
    # LLM-Judge
    # ──────────────────────────────────────────────────────────────────────────

    async def judge_dialogue(
        self,
        script: NewsScript,
        articles: List[RawArticle],
        language: str = "English",
    ) -> JudgeScore:
        """Evalúa la calidad del guion generado y devuelve un JudgeScore.

        Dimensiones evaluadas (0-10 cada una, promedio final):
        - Cobertura de noticias
        - Calidad y naturalidad del diálogo
        - Preparación para TTS (sin Markdown ni efectos de sonido)
        - Duración estimada plausible
        """
        template = self.jinja_env.get_template("judge_script.jinja2")
        prompt = template.render(script=script, articles=articles, language=language)
        logger.debug("Judge Prompt:\n%s", prompt)

        response = await self.mistral_client.chat.complete_async(
            model=self._judge_model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
        )

        raw = response.choices[0].message.content
        judge_score = JudgeScore.model_validate_json(raw)

        logger.info(
            "Judge score: %.1f/10 | needs_rewrite: %s | %s",
            judge_score.score,
            judge_score.needs_rewrite,
            judge_score.justification[:120],
        )
        if judge_score.needs_rewrite and judge_score.feedback:
            logger.warning("Judge recomienda reescritura: %s", judge_score.feedback)

        return judge_score

    # ──────────────────────────────────────────────────────────────────────────
    # Generación del cover (imagen)
    # ──────────────────────────────────────────────────────────────────────────

    async def generate_cover(self, script: NewsScript, language: str = "English") -> str:
        visual_brief = await self._generate_visual_brief(script, language)
        logger.debug("Cover Podcast Prompt:\n%s", visual_brief)

        cover = await self._create_hf_image(visual_brief)

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            cover.save(tmp, format="PNG")
            temp_path = tmp.name

        logger.info("Cover temporal generado en: %s", temp_path)
        return temp_path

    async def _generate_visual_brief(self, script: NewsScript, language: str) -> str:
        """Mistral actúa como Director de Arte generando el prompt para FLUX.1."""
        template = self.jinja_env.get_template("cover_art_prompt.jinja2")
        prompt = template.render(script=script, language=language)

        response = await self.mistral_client.chat.complete_async(
            model="mistral-large-latest",
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content

    async def _create_hf_image(
        self, visual_prompt: str, width: int = 1024, height: int = 1024, seed: int = 42
    ) -> Image.Image:
        image = self.hf_client.text_to_image(
            visual_prompt,
            model=os.getenv("HF_IMAGE_MODEL", "black-forest-labs/FLUX.1-schnell"),
            width=width,
            height=height,
            seed=seed,
        )
        return image