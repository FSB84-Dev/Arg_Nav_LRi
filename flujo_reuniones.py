import anthropic
import base64
import json
import logging
from datetime import datetime
from config import CLAUDE_API_KEY
from router import decidir_ruta_audio

logger = logging.getLogger(__name__)

PROMPT_REUNION = """Eres un asistente comercial especializado en Aragon, Navarra y La Rioja.
Escucha este audio de reunion comercial y extrae la informacion en JSON.

IMPORTANTE:
- FechaReunion: fecha en que ocurrio la reunion (NO hoy). Si no se menciona, usa null.
- tipo: "Cliente" si ya es cliente, "Objetivo" si es prospecto
- estado_lead: Nuevo, Activo, Caliente, Frio o Cerrado

Responde SOLO con JSON valido, sin texto adicional:
{
  "fecha_reunion": "DD/MM/YYYY o null",
  "empresa": "nombre empresa",
  "contacto": "nombre contacto",
  "tipo": "Cliente o Objetivo",
  "resumen": "resumen breve",
  "proximos_pasos": "acciones a tomar",
  "estado_lead": "estado",
  "objeciones": "preocupaciones o null",
  "productos": "productos/modelos tratados o null"
}"""


async def procesar_audio_reunion(audio_bytes: bytes, duracion: int = 0) -> dict:
    ruta = decidir_ruta_audio(duracion_segundos=duracion, tamano_bytes=len(audio_bytes))
    logger.info(f"INFO:flujo_reuniones:Ruta seleccionada: {ruta}")
    modelo = "claude-haiku-20240307" if ruta == "simple" else "claude-sonnet-4-5"
    client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)
    audio_b64 = base64.standard_b64encode(audio_bytes).decode("utf-8")
    try:
        respuesta = client.messages.create(
            model=modelo,
            max_tokens=1024,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": PROMPT_REUNION},
                    {
                        "type": "document",
                        "source": {
                            "type": "base64",
                            "media_type": "audio/mpeg",
                            "data": audio_b64
                        }
                    }
                ]
            }]
        )
        texto = respuesta.content[0].text.strip()
        if texto.startswith("```"):
            lineas = texto.split("\n")
            texto = "\n".join(lineas[1:-1])
        datos = json.loads(texto)
        datos["fecha_procesado"] = datetime.now().strftime("%Y-%m-%d %H:%M")
        datos["modelo_usado"] = modelo
        return {"ok": True, "datos": datos}
    except Exception as e:
        logger.error(f"Error procesando audio: {e}")
        return {"ok": False, "error": str(e)}


def formatear_confirmacion(resultado: dict) -> str:
    d = resultado.get("datos", {})
    lineas = [
        "Reunion registrada",
        "",
        f"Empresa: {d.get('empresa', 'No detectada')}",
        f"Contacto: {d.get('contacto', 'No detectado')}",
        f"Fecha reunion: {d.get('fecha_reunion', 'No indicada')}",
        f"Tipo: {d.get('tipo', 'Objetivo')}",
        f"Estado: {d.get('estado_lead', 'Nuevo')}",
        "",
        f"Resumen: {d.get('resumen', '')}",
        "",
        f"Proximos pasos: {d.get('proximos_pasos', '')}",
    ]
    if d.get("objeciones"):
        lineas.append(f"Objeciones: {d.get('objeciones')}")
    if d.get("productos"):
        lineas.append(f"Productos: {d.get('productos')}")
    return "\n".join(lineas)
