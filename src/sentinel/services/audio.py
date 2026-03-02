import io
import os
import tempfile
from typing import Dict, Optional
from elevenlabs.client import ElevenLabs
from pydub import AudioSegment
from sentinel.interfaces.schemas import NewsScript, SpeakerSettings
import sentinel.utils.config  # noqa: F401 – carga el .env al importar
from sentinel.utils.logger import get_logger

logger = get_logger(__name__)


class VoiceEngine:
    def __init__(self):
        self.client = ElevenLabs(api_key=os.getenv("ELEVEN_API_KEY"))
        self.model_id = os.getenv("ELEVEN_MODEL_ID", "eleven_multilingual_v2")
        self.default_voices = {
            "Alex": SpeakerSettings(
                voice_id=os.getenv("VOICE_ID_ALEX", "pNInz6obpgDQGcFma_JgB")
            ),
            "Sam": SpeakerSettings(
                voice_id=os.getenv("VOICE_ID_SAM", "EXAVITQu4vr4xnSDxMaL")
            )
        }

    async def generate_podcast_audio(
        self, 
        script: NewsScript, 
        voice_mapping: Optional[Dict[str, SpeakerSettings]] = None
    ) -> str:
        active_voices = voice_mapping or self.default_voices
        combined_audio = AudioSegment.empty()
        silence = AudioSegment.silent(duration=500)

        for line in script.dialogue:
            speaker_config = active_voices.get(
                line.speaker,
                list(active_voices.values())[0]
            )

            voice_settings = speaker_config.to_eleven_labs()
            # 1. Obtenemos el stream de ElevenLabs
            audio_generator = self.client.text_to_speech.convert(
                voice_id=speaker_config.voice_id,
                text=line.text,
                model_id=self.model_id,
                output_format="mp3_44100_128",
                voice_settings=voice_settings
            )
            logger.debug("Audio generado para speaker: %s", line.speaker)

            # 2. Procesamos en memoria con BytesIO
            audio_bytes = b"".join(audio_generator)
            segment = AudioSegment.from_file(io.BytesIO(audio_bytes), format="mp3")
            combined_audio += segment + silence

        # 3. Guardado en un archivo temporal
        # Usamos delete=False para que el archivo persista tras cerrar el objeto 
        # y así la interfaz web pueda leerlo. Lo borraremos manualmente o al cerrar la app.
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
        combined_audio.export(temp_file.name, format="mp3")
        
        logger.info("Podcast temporal generado en: %s", temp_file.name)
        return temp_file.name