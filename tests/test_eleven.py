import os
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs

# 1. Cargar variables del .env
load_dotenv()

def test_voice_api():
    api_key = os.getenv("ELEVEN_API_KEY")
    # Usamos la voz por defecto "Adam" si no tienes una en el .env
    voice_id = os.getenv("VOICE_ID_ALEX", "pNInz6obpgDQGcFmaJgB") 
    model_id = os.getenv("ELEVEN_MODEL_ID", "eleven_multilingual_v2")

    print(f"🧪 Probando ElevenLabs...")
    print(f"🔑 API Key detectada: {'SÍ' if api_key else 'NO'}")
    print(f"🗣️ Voz: {voice_id} | 🤖 Modelo: {model_id}")

    try:
        client = ElevenLabs(api_key=api_key)
        
        # 2. Intento de generación simple (Hardcoded)
        print("⏳ Generando audio de prueba...")
        audio_generator = client.text_to_speech.convert(
            voice_id=voice_id,
            text="Hola, esto es una prueba de Sentinel para el hackatón de Mistral. Si escuchas esto, el API funciona.",
            model_id=model_id,
            output_format="mp3_44100_128"
        )

        # 3. Guardar el resultado para verificarlo
        audio_bytes = b"".join(audio_generator)
        with open("test_output.mp3", "wb") as f:
            f.write(audio_bytes)
        
        print("✅ ¡Éxito! Se ha generado 'test_output.mp3'.")
        print(f"📊 Tamaño del archivo: {len(audio_bytes) / 1024:.2f} KB")

    except Exception as e:
        print(f"❌ Error detectado: {str(e)}")
        if "quota" in str(e).lower():
            print("💡 Consejo: Parece que te has quedado sin caracteres en la cuenta gratuita.")
        elif "not found" in str(e).lower():
            print("💡 Consejo: Revisa si el VOICE_ID es correcto en tu cuenta de ElevenLabs.")

if __name__ == "__main__":
    test_voice_api()