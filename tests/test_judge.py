"""
Test de integración del LLM-Judge.
Requiere MISTRAL_API_KEY y JUDGE_MODEL en el entorno (o .env).
"""
import asyncio
import os
import pytest
from dotenv import load_dotenv

load_dotenv()


@pytest.mark.asyncio
async def test_judge_dialogue_returns_valid_score():
    """El judge devuelve un JudgeScore con score entre 0 y 10."""
    from sentinel.services.llm import LLMService
    from sentinel.interfaces.schemas import NewsScript, RawArticle, JudgeScore

    if not os.getenv("MISTRAL_API_KEY"):
        pytest.skip("MISTRAL_API_KEY no disponible")

    # Script mínimo hardcodeado para no llamar a HN ni a la pipeline completa
    script = NewsScript(
        headline="AI Takes Over the World, Again",
        summaries=[],
        dialogue=[
            {"speaker": "Alex", "text": "Welcome to Sentinel Daily. Today we cover AI breakthroughs."},
            {"speaker": "Sam", "text": "That's right Alex! The new models are amazing and changing everything fast."},
            {"speaker": "Alex", "text": "Indeed. The implications for enterprise are significant."},
            {"speaker": "Sam", "text": "And the open source community is moving incredibly quickly too!"},
        ],
        estimated_duration=30,
    )

    articles = [
        RawArticle(
            id=1,
            title="AI Breakthroughs in 2026",
            url="https://example.com/ai-2026",
            source="Hacker News",
            content_summary="Major AI labs released powerful new models that outperform previous SOTA on all benchmarks.",
        )
    ]

    llm_service = LLMService()
    judge_score: JudgeScore = await llm_service.judge_dialogue(
        script=script, articles=articles, language="English"
    )

    assert isinstance(judge_score, JudgeScore), "Debe devolver un JudgeScore"
    assert 0.0 <= judge_score.score <= 10.0, f"Score fuera de rango: {judge_score.score}"
    assert isinstance(judge_score.justification, str) and len(judge_score.justification) > 10
    assert isinstance(judge_score.needs_rewrite, bool)
    print(f"\n✅ Judge score: {judge_score.score}/10 — {judge_score.justification}")


@pytest.mark.asyncio
async def test_judge_disabled_returns_none():
    """Con JUDGE_ENABLED=false, generate_dialogue devuelve None como judge_score."""
    import os
    os.environ["JUDGE_ENABLED"] = "false"

    # Re-importamos para que el __init__ lea la nueva variable
    import importlib
    import sentinel.services.llm as llm_module
    importlib.reload(llm_module)

    from sentinel.services.llm import LLMService
    from sentinel.interfaces.schemas import RawArticle

    if not os.getenv("MISTRAL_API_KEY"):
        pytest.skip("MISTRAL_API_KEY no disponible")

    llm_service = llm_module.LLMService()
    assert llm_service._judge_enabled is False, "El judge debería estar deshabilitado"
