from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional

class RawArticle(BaseModel):
    """Información bruta extraída de la fuente (Hacker News/RSS)"""
    id: int
    title: str
    url: Optional[HttpUrl] = None
    source: str
    content_summary: str  # Los primeros párrafos o el snippet

class ReferenceArticle(BaseModel):
    """Información bruta extraída de la fuente (Hacker News/RSS)"""
    id: int
    title: str
    url: Optional[HttpUrl] = None
    brief: str  # Los primeros párrafos o el snippet

class DialogueLine(BaseModel):
    speaker: str = Field(description="Nombre del locutor (Alex o Sam)")
    text: str = Field(description="Lo que dice el locutor (sin tecnicismos extremos)")

class NewsScript(BaseModel):
    """El guion procesado por Mistral para ser leído"""
    headline: str
    summaries: List[ReferenceArticle] = Field(description="Lista secuencial de articulos")
    dialogue: List[DialogueLine] = Field(description="Lista secuencial de la conversación")
    estimated_duration: int

class JudgeScore(BaseModel):
    """La evaluación del LLM-Judge"""
    score: float = Field(ge=0, le=10, description="Puntuación de 0 a 10")
    justification: str = Field(description="Breve explicación de la nota")
    needs_rewrite: bool = Field(description="Indica si el guion debe corregirse")
    feedback: Optional[str] = Field(None, description="Instrucciones para la corrección")

class FinalPodcast(BaseModel):
    """El output final listo para la UI"""
    audio_path: str
    cover_path: str
    transcript: NewsScript
    language: str
    score: float
    sources: List[RawArticle]


class SpeakerSettings(BaseModel):
    voice_id: str
    stability: float = Field(default=0.35, ge=0.0, le=1.0)
    similarity_boost: float = Field(default=0.75, ge=0.0, le=1.0)
    style: float = Field(default=0.15, ge=0.0, le=1.0)
    use_speaker_boost: bool = True

    def to_eleven_labs(self):
        """Convierte al formato exacto que espera la SDK de ElevenLabs"""
        return {
            "stability": self.stability,
            "similarity_boost": self.similarity_boost,
            "style": self.style,
            "use_speaker_boost": self.use_speaker_boost
        }