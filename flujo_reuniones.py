import anthropic
import json
import logging
import tempfile
import os
from datetime import datetime
from openai import OpenAI
from config import CLAUDE_API_KEY, OPENAI_API_KEY
from router import decidir_ruta_audio

logger = logging.getLogger(__name__)

PROMPT_EXTRACCION = """Eres un asistente comercial especializado en Aragon, Navarra y La Rioja.
Analiza esta transcripcion de una reunion comercial y extrae la informacion en JSON.

IMPORTANTE:
- fecha_reunion: fecha en que ocurrio la reunion (NO hoy). Si no se menciona, usa null.
- tipo: "Cliente" si ya es cliente, "Objetivo" si es prospecto nuevo
- estado_lead: Nuevo, Activo, Caliente, Frio o Cerrado

Transcripcion:
{transcripcion}

Responde SOLO con JSON valido, sin texto adicional ni backticks:
{{
  "fecha_reunion": "DD/MM/YYYY o null",
  "empresa": "nombre empresa",
  "contacto": "nombre contacto",
  "tipo": "Cliente o Objetivo",
  "resumen": "resumen breve de la reunion",
  "proximos_pasos": "acciones a tomar",
  "estado_lead": "estado del lead",
  "objeciones": "preocupaciones del cliente o null",
  "productos": "productos o modelos tratados o null"
}}"""


async def transcribir_con_whisper(audio_bytes: bytes) -> str:
    client = OpenAI(api_key=OPENAI_API_KEY)
    with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as f:
        f.write(audio_bytes)
        temp_path = f.name
    try:
        with open(temp_path, "rb") as audio_file:
            transcripcion = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="es"
            )
        return transcripcion.text
    finally:
        os.unlink(temp_path)


async def extraer_datos_con_claude(transcripcion: str, modelo: str) -> dict:
    client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)
    prompt = PROMPT_EXTRACCION.format(transcripcion=transcripcion)
    respuesta = client.messages.create(
        model=modelo,
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}]
    )
    texto = respuesta.content[0].text.strip()
    if texto.startswith("```"):
        lineas = texto.split("\n")
        texto = "\n".join(lineas[1:-1])
    return json.loads(texto)


async def procesar_audio_reunion(audio_bytes: bytes, duracion: int = 0) -> dict:
    ruta = decidir_ruta_audio(duracion_segundos=duracion, tamano_bytes=len(audio_bytes))
    logger.info(f"INFO:flujo_reuniones:Ruta seleccionada: {ruta}")
    modelo = "claude-haiku-4-5" if ruta == "simple" else "claude-sonnet-4-5"
    try:
        logger.info("Transcribiendo audio con Whisper...")
        transcripcion = await transcribir_con_whisper(audio_bytes)
        logger.info(f"Transcripcion: {transcripcion[:100]}...")
        logger.info("Extrayendo datos con Claude...")
        datos = await extraer_datos_con_claude(transcripcion, modelo)
        datos["fecha_procesado"] = datetime.now().strftime("%Y-%m-%d %H:%M")
        datos["transcripcion"] = transcripcion
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
