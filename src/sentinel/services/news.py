import json
import httpx
import asyncio
from typing import List
from sentinel.interfaces.schemas import RawArticle
from trafilatura import extract, fetch_url
from sentinel.utils.logger import get_logger

logger = get_logger(__name__)


async def get_article_content(url: str) -> str:
    """Comprueba, descarga y extrae el contenido de una URL."""
    try:
        # 1. Intentamos descargar la web
        # Trafilatura tiene un fetch_url interno que maneja timeouts y user-agents
        downloaded = fetch_url(url)
        
        if downloaded is None:
            return "Error: No se pudo acceder a la URL o el contenido no está disponible."

        # 2. Extraemos el texto limpio (sin HTML, sin menús)
        content = extract(downloaded, include_comments=False, no_fallback=False)
        
        if not content or len(content) < 100:
            return "Error: El contenido extraído es demasiado corto o inválido."

        return content  # Retornamos los primeros 3000 caracteres para el LLM
        
    except Exception as e:
        logger.exception("Error crítico al procesar la noticia: %s", url)
        return f"Error crítico al procesar la noticia: {str(e)}"


class NewsService:
    def __init__(self):
        self.base_url = "https://hacker-news.firebaseio.com/v0"

    async def get_top_stories(self, limit: int = 10) -> List[RawArticle]:
        async with httpx.AsyncClient() as client:
            # 1. Obtener los IDs de las mejores historias actuales
            resp = await client.get(f"{self.base_url}/topstories.json")
            all_ids = resp.json()[:50]
            
            articles = []
            
            # 2. Recorremos los IDs hasta alcanzar el 'limit' de artículos VÁLIDOS
            for _id in all_ids:
                if len(articles) >= limit:
                    break
                
                # Obtenemos metadata del item
                item_resp = await client.get(f"{self.base_url}/item/{_id}.json")
                data = item_resp.json()
                
                url = data.get("url")
                if not url:
                    continue  # Saltamos si no tiene link externo (ej. posts de "Ask HN")

                # 3. Intentamos extraer el contenido real
                title_preview = (data.get("title") or "")[:40]
                logger.info("Intentando extraer: %s...", title_preview)
                content = await get_article_content(url)

                # 4. Verificación de calidad: ¿Es contenido real o un error?
                if content and "Error:" not in content and len(content) > 250:
                    articles.append(RawArticle(
                        id=data.get("id"),
                        title=data.get("title", "No Title"),
                        url=url,
                        source="Hacker News",
                        content_summary=content[:3500]  # Capamos para no saturar el LLM
                    ))
                    logger.info("Artículo añadido (%d/%d): %s", len(articles), limit, data.get("title", ""))
                else:
                    logger.warning("Fallo en extracción, buscando siguiente: %s", url)

            return articles


# Test rápido
if __name__ == "__main__":
    service = NewsService()
    stories = asyncio.run(service.get_top_stories(3))
    for idx, s in enumerate(stories):
        logger.info("🔥 %s (%s)", s.title, s.url)
        with open(f'{s.id}.json', "w", encoding="utf-8") as f:
            f.write(s.model_dump_json(indent=4))