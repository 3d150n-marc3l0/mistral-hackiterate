import streamlit as st
import asyncio
import os
import time
import json
from typing import List
from datetime import datetime
from sentinel.core.pipeline import SentinelPipeline
from sentinel.interfaces.schemas import FinalPodcast, SpeakerSettings
import pandas as pd
from dotenv import load_dotenv
from sentinel.utils.logger import get_logger

load_dotenv()

logger = get_logger(__name__)

OUTPUT_DIR = "outputs"

voice_setting = {}
voice_setting["Alex"] = {
    "voice_id": os.getenv("VOICE_ID_ALEX", "pNInz6obpgDQGcFmaJgB") 
}
voice_setting["Sam"] = {
    "voice_id": os.getenv("VOICE_ID_SAM", "EXAVITQu4vr4xnSDxMaL")
}

def save_to_disk(podcast_data: FinalPodcast) -> FinalPodcast:
    """Guarda el objeto FinalPodcast en una carpeta única."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(OUTPUT_DIR, timestamp)
    os.makedirs(path, exist_ok=True)
    
    # Mover/Guardar Audio
    final_audio_path = os.path.join(path, "audio.mp3")
    os.rename(podcast_data.audio_path, final_audio_path)

    # Mover/Guardar Cover
    final_cover_path = os.path.join(path, "cover.png")
    os.rename(podcast_data.cover_path, final_cover_path)

    # Guardar JSON (Metadata + Script)
    podcast_data = podcast_data.model_copy(update={"audio_path": final_audio_path})
    podcast_data = podcast_data.model_copy(update={"cover_path": final_cover_path})
    with open(os.path.join(path, "metadata.json"), "w") as f:
        #f.write(podcast_data.transcript.model_dump_json(indent=4))
        f.write(podcast_data.model_dump_json(indent=4))

    return podcast_data

def load_history() -> List[FinalPodcast]:
    """Lee todas las carpetas en outputs y devuelve una lista de podcasts."""
    history = []
    if not os.path.exists(OUTPUT_DIR): return []
    
    # Ordenar por carpeta (nombre = timestamp) de más reciente a más antiguo
    folders = sorted(os.listdir(OUTPUT_DIR), reverse=True)
    for folder in folders:
        path = os.path.join(OUTPUT_DIR, folder)
        meta_path = os.path.join(path, "metadata.json")
        audio_path = os.path.join(path, "audio.mp3")
        
        if os.path.exists(meta_path) and os.path.exists(audio_path):
            with open(meta_path, "r") as f:
                data = json.load(f)
                logger.debug("Historial cargado: %s", folder)
                data["audio_path"] = audio_path
                podcast_data = FinalPodcast.model_validate(data)
                history.append({
                    "id": folder,
                    "podcast_data": podcast_data,
                    "audio_path": audio_path
                })
    return history

# 1. Al principio de la app, inicializamos el estado si no existe
if 'podcast_ready' not in st.session_state:
    st.session_state.podcast_ready = False
    st.session_state.podcast_data = None
if 'streamed' not in st.session_state:
    st.session_state.streamed = False
# Cargamos lo que haya en disco al arrancar
if 'history' not in st.session_state:
    st.session_state.history = load_history()
if 'view' not in st.session_state:
    st.session_state.view = "generator"    

# Configuración estética
st.set_page_config(
    page_title="Sentinel Daily | AI Podcast",
    page_icon="🎙️",
    layout="wide"
)

# Estilo personalizado para las tarjetas de noticias
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stAudio { margin-top: 20px; }
    .speaker-alex { color: #4facfe; font-weight: bold; }
    .speaker-sam { color: #00f2fe; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# Inicialización del cerebro del proyecto
@st.cache_resource
def init_pipeline() -> SentinelPipeline:
    return SentinelPipeline()

pipeline = init_pipeline()

# --- INTERFAZ ---
st.title("🎙️ Sentinel Daily")
st.caption("AI-Driven Multilingual Tech News Podcast powered by Mistral Large 3")

with st.sidebar:
    st.header("🎛️ Control Panel")


    language = st.selectbox(
        "Podcast Language",
        ["English", "Spanish", "French", "German", "Italian"],
        help="Mistral will adapt the script and idioms to the chosen language."
    )
    
    news_count = st.slider("Stories to analyze", 1, 5, 3)

    st.divider()
    st.markdown("### 🎙️ Voice Tuning")
    
    with st.expander("👤 Alex (The Analyst)"):
        voice_setting["Alex"]["stability"] = st.slider("Stability ", 0.0, 1.0, 0.35, key="alex_stab")
        voice_setting["Alex"]["similarity"] = st.slider("Clarity ", 0.0, 1.0, 0.75, key="alex_sim")
        voice_setting["Alex"]["style"] = st.slider("Style ", 0.0, 1.0, 0.20, key="alex_style")

    with st.expander("👩‍💻 Sam (The Explorer)"):
        voice_setting["Sam"]["stability"] = st.slider("Stability", 0.0, 1.0, 0.25, key="sam_stab") # Más baja = más nervio
        voice_setting["Sam"]["similarity"] = st.slider("Clarity", 0.0, 1.0, 0.80, key="sam_sim")
        voice_setting["Sam"]["style"] = st.slider("Style", 0.0, 1.0, 0.45, key="sam_style")
    
    st.divider()
    
    # SECCIÓN DE NAVEGACIÓN
    st.subheader("🚀 Navigation")
    if st.button("➕ Create New Podcast", use_container_width=True):
        st.session_state.view = "generator"
        st.rerun()
    
    if st.button("📚 Show Library", use_container_width=True):
        st.session_state.view = "library"
        st.rerun()

    st.divider()
    st.markdown("### Architecture")
    st.info("""
    - **LLM:** Mistral Large 3
    - **Voice:** ElevenLabs Multilingual v2
    - **Quality:** LLM-as-a-Judge enabled
    """)

# --- FLUJO PRINCIPAL ---
if st.session_state.view == "generator":
    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("📡 Generate Broadcast")
        if st.button("🚀 Start Production New", use_container_width=True):
            with st.status("Sentinel is working...", expanded=True) as status:
                try:
                    # 1. Ejecución del proceso
                    st.write("🔍 Fetching latest tech trends...")
                    voice_mapping = {} 
                    for voice_name, voice_conf in voice_setting.items():
                        logger.debug("voice_name: %s, voice_conf: %s", voice_name, voice_conf)
                        voice_mapping[voice_name] = SpeakerSettings.model_validate(voice_conf)
                    podcast_data = asyncio.run(pipeline.run_full_process(
                        language=language, 
                        limit=news_count,
                        voice_mapping=voice_mapping
                    ))

                    # Guardamos el resultado en el estado global antes de terminar el bloque
                    st.session_state.podcast_data = podcast_data
                    st.session_state.podcast_ready = True
                    st.session_state.streamed = False # Reset para el nuevo podcast
                    status.update(label="✅ Broadcast Ready!", state="complete")
                    st.rerun()
                except Exception as e:
                    st.error(f"Pipeline Error: {e}")

        # --- ZONA DE RESULTADOS (Dentro de col1) ---
        if st.session_state.podcast_data:
            data = st.session_state.podcast_data
            st.divider()
            #st.success(f"**Episode:** {data.script_body['headline']}")
            st.success(f"**Episode:** {data.transcript.headline}")
            
            st.image(
                data.cover_path, 
                caption=f"Sentinel Podcast - {data.transcript.headline}",
                use_container_width=True
            )
            with open(data.audio_path, "rb") as f:
                audio_bytes = f.read()
                st.audio(audio_bytes, format="audio/mp3")

            st.divider()
            if st.button("🚀 Save", use_container_width=True):
                data = save_to_disk(data)
                st.session_state.podcast_data = data
                st.rerun()

            # 3. Sección de Referencias (Summaries + Links)
            st.markdown("### 📰 Featured Stories")
            st.caption("Deep dive into the sources analyzed in this broadcast:")

            # Iteramos sobre los resúmenes que generó Mistral
            for item in data.transcript.summaries:
                with st.expander(f"🔹 {item.title}"):
                    # Mostramos el resumen ejecutivo
                    st.write(item.brief)
                    
                    # Botón pequeño o link para ir a la fuente
                    st.markdown(f"🔗 [Read full article on source]({item.url})")

    with col2:
        st.subheader("📜 Live Transcript")
        if st.session_state.podcast_data:
            data = st.session_state.podcast_data
            # Usamos un contenedor vacío para el efecto de escritura
            transcript_area = st.empty()
            full_text = ""
            
            # Si es la primera vez que vemos estos datos, hacemos el streaming
            if not st.session_state.streamed:
                for line in data.transcript.dialogue:
                    speaker = line.speaker
                    text = line.text
                    icon = "🔵" if speaker == "Alex" else "🟢"
                    
                    header = f"\n\n**{icon} {speaker}:** "
                    full_text += header
                    
                    # Efecto palabra por palabra
                    for word in text.split():
                        full_text += word + " "
                        transcript_area.markdown(full_text + "▌")
                        time.sleep(0.05) # Velocidad del "locutor"
                
                st.session_state.streamed = True  # Marcamos como leído
                transcript_area.markdown(full_text)  # Quitamos el cursor final
            else:
                # Si ya se hizo el streaming (ej. al pulsar "Download"), lo mostramos del tirón
                for line in data.transcript.dialogue:
                    st.markdown(f"{'🔵' if line.speaker == 'Alex' else '🟢'} **{line.speaker}:** {line.text}")
        else:
            st.info("The transcript will appear here once generated.")

# --- VISTA: BIBLIOTECA (La Tabla que pedías) ---
elif st.session_state.view == "library":
    st.title("📚 Podcast Archive")
    
    history = load_history() # Función que lee la carpeta 'outputs/'
    
    if not history:
        st.info("No hay podcasts guardados todavía.")
    else:
        # Preparamos los datos para la tabla (mostramos info relevante)
        table_data = []
        for i, p in enumerate(history):
            data = p['podcast_data']
            table_data.append({
                "Date": p['id'], # El nombre de la carpeta es el timestamp
                "Headline": data.transcript.headline,
                "Language": data.language,
                "Articles": len(data.transcript.summaries),
                "Index": i
            })
        
        df = pd.DataFrame(table_data)
        
        # Renderizamos la tabla fila por fila para añadir el botón de carga
        cols = st.columns([2, 5, 1, 1, 2])
        cols[0].write("**Date**")
        cols[1].write("**Headline**")
        cols[2].write("**Language**")
        cols[3].write("**News**")
        cols[4].write("**Action**")
        st.divider()

        for i, row in df.iterrows():
            c1, c2, c3, c4, c5 = st.columns([2, 5, 1, 1, 2])
            c1.write(row["Date"])
            c2.write(row["Headline"])
            c3.write(row["Language"])
            c4.write(row["Articles"])
            
            # El botón mágico para cargar este podcast específico
            if c5.button("📂 Load", key=f"load_{i}"):
                st.session_state.selected_podcast = history[i]
                st.session_state.view = "viewer" # Nueva vista para ver el detalle
                st.rerun()
# --- VISTA: VISUALIZADOR (Detalle del podcast seleccionado) ---
elif st.session_state.view == "viewer":
    p = st.session_state.selected_podcast
    data = p['podcast_data']
    
    if st.button("⬅️ Back to Library"):
        st.session_state.view = "library"
        st.rerun()

    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("📡 Podcast Details")
        
        st.divider()
        if data.cover_path and os.path.exists(data.cover_path) and os.path.isfile(data.cover_path):
            st.image(
                data.cover_path, 
                caption=f"Sentinel Podcast - {data.transcript.headline}",
                use_container_width=True
            )
        with open(data.audio_path, "rb") as f:
            audio_bytes = f.read()
            st.audio(audio_bytes, format="audio/mp3")
        
        st.divider()
        # 3. Sección de Referencias (Summaries + Links)
        st.markdown("### 📰 Featured Stories")
        st.caption("Deep dive into the sources analyzed in this broadcast:")

        # Iteramos sobre los resúmenes que generó Mistral
        for item in data.transcript.summaries:
            with st.expander(f"🔹 {item.title}"):
                # Mostramos el resumen ejecutivo
                st.write(item.brief)
                
                # Botón pequeño o link para ir a la fuente
                st.markdown(f"🔗 [Read full article on source]({item.url})")

    with col2:
        st.subheader("📜 Live Transcript")
        transcript_area = st.empty()
        full_text = ""
        if data.transcript.dialogue:
            # Mostramos el diálogo de forma estética
            for line in data.transcript.dialogue:
                speaker = line.speaker
                text = line.text
                icon = "🔵" if speaker == "Alex" else "🟢"
                
                header = f"\n\n**{icon} {speaker}:** "
                full_text += header
                
                # Efecto palabra por palabra
                for word in text.split():
                    full_text += word + " "
                    transcript_area.markdown(full_text + "▌")
                    time.sleep(0.05)  # Velocidad del "locutor"
            
            transcript_area.markdown(full_text)  # Quitamos el cursor final
        else:
            st.info("Start the production to see the transcript here.")
# Imagen del flujo para que el jurado entienda la ingeniería detrás