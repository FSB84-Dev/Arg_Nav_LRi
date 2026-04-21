"""
FLUJO REUNIONES — Audio -> Transcripcion -> Google Sheets
"""
import anthropic
import base64
import json
import logging
from datetime import datetime
from config import CLAUDE_API_KEY
from router import decidir_ruta_audio

logger = logging.getLogger(__name__)
client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)

PROMPT_SIMPLE = """Eres un asistente comercial. Escucha este audio de reunion y extrae:
- empresa: nombre de la empresa mencionada
- contacto: nombre de la persona
- resumen: resumen breve de la reunion (max 100 palabras)
- proximos_pasos: que hay que hacer despues
- objeciones: preocupaciones del cliente
- estado_lead: (Nuevo/Activo/Caliente/Frio/Cerrado)

Responde SOLO con JSON valido, sin texto adicional."""

async def procesar_audio_reunion(audio_bytes: bytes, duracion: int = 0) -> dict:
    ruta = decidir_ruta_audio(duracion_segundos=duracion, tamano_bytes=len(audio_bytes))
    logger.info(f"Ruta seleccionada: {ruta}")

    modelo = "claude-haiku-4-5" if ruta == "simple" else "claude-sonnet-4-5"
    audio_b64 = base64.standard_b64encode(audio_bytes).decode("utf-8")

    try:
        respuesta = client.messages.create(
            model=modelo,
            max_tokens=1024,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": PROMPT_SIMPLE},
                    {"type": "document", "source": {
                        "type": "base64",
                        "media_type": "audio/ogg",
                        "data": audio_b64
                    }}
                ]
            }]
        )
        texto = respuesta.content[0].text
        datos = json.loads(texto)
        datos["fecha"] = datetime.now().strftime("%Y-%m-%d %H:%M")
        datos["modelo_usado"] = modelo
        return {"ok": True, "datos": datos}
    except Exception as e:
        logger.error(f"Error procesando audio: {e}")
        return {"ok": False, "error": str(e)}

def formatear_confirmacion(datos: dict) -> str:
    d = datos.get("datos", {})
    return (
        f"Reunion registrada\n\n"
        f"Empresa: {d.get('empresa', 'No detectada')}\n"
        f"Contacto: {d.get('contacto', 'No detectado')}\n"
        f"Estado: {d.get('estado_lead', 'Nuevo')}\n\n"
        f"Resumen: {d.get('resumen', '')}\n\n"
        f"Proximos pasos: {d.get('proximos_pasos', '')}"
    )
