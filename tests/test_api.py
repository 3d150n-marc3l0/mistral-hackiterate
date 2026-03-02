import os
import asyncio
from mistralai import Mistral
from dotenv import load_dotenv

async def test_mistral_connection():
    # Cargar variables de entorno
    load_dotenv()
    api_key = os.getenv("MISTRAL_API_KEY")
    
    if not api_key:
        print("❌ Error: No se encontró MISTRAL_API_KEY en el entorno.")
        return

    client = Mistral(api_key=api_key)

    print("📡 Conectando con Mistral...")
    try:
        # Probamos con Mistral Small (rápido y barato para tests)
        chat_response = await client.chat.complete_async(
            model="mistral-small-latest",
            messages=[
                {"role": "user", "content": "Hola, ¿estás operativo? Responde solo con 'OK' y tu nombre de modelo."},
            ]
        )
        print(f"✅ Conexión exitosa!")
        print(f"🤖 Respuesta: {chat_response.choices[0].message.content}")
        
    except Exception as e:
        print(f"❌ Error al conectar: {e}")

if __name__ == "__main__":
    asyncio.run(test_mistral_connection())