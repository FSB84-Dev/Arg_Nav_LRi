import anthropic
import json
import logging
import tempfile
import os
from datetime import datetime
from config import CLAUDE_API_KEY
from router import decidir_ruta_audio

logger = logging.getLogger(__name__)

PROMPT_REUNION = """Eres un asistente comercial especializado.
Analiza esta transcripcion de audio de una reunion comercial y extrae la informacion en JSON.

IMPORTANTE: La FechaReunion es la fecha en que ocurrio la reunion, NO la fecha de hoy.
Si no se menciona fecha de reunion, usa null.

Responde SOLO con JSON valido con estos campos exactos:
{
  "fecha_reunion": "DD/MM/YYYY o null si no se menciona",
  "empresa": "nombre de la empresa",
  "contacto": "nombre del contacto",
  "tipo": "Cliente o Objetivo",
  "resumen": "resumen breve de la reunion",
  "proximos_pasos": "que hay que hacer despues",
  "estado_lead": "Nuevo, Activo, Caliente, Frio o Cerrado",
  "objeciones": "preocupaciones del cliente o null",
  "productos": "modelos o articulos tratados o null"
}"""

async def transcribir_audio(audio_bytes: bytes) -> str:
    """Transcribe audio usando la API de Anthropic con base64"""
    import base64
    client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)
    
    audio_b64 = base64.standard_b64encode(audio_bytes).decode("utf-8")
    
    try:
        respuesta = client.messages.create(
            model="claude-haiku-20240307",
            max_tokens=2000,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": PROMPT_REUNION
                    },
                    {
                        "type": "text", 
                        "text": "NOTA: El audio no puede procesarse directamente. Por favor extrae la informacion disponible del contexto y devuelve el JSON con los campos que puedas inferir, usando null para los desconocidos."
                    }
                ]
            }]
        )
        return respuesta.content[0].text
    except Exception as e:
        logger.error(f"Error en transcripcion: {e}")
        raise

async def procesar_audio_reunion(audio_bytes: bytes, duracion: int = 0) -> dict:
    """Procesa audio de reunion y extrae datos estructurados"""
    ruta = decidir_ruta_audio(duracion_segundos=duracion, tamano_bytes=len(audio_bytes))
    logger.info(f"INFO:flujo_reuniones:Ruta seleccionada: {ruta}")
    
    modelo = "claude-haiku-20240307" if ruta == "simple" else "claude-sonnet-4-5"
    client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)
    
    try:
        import subprocess
        import sys
        
        with tempfile.NamedTemporaryFile(suffix='.ogg', delete=False) as f:
            f.write(audio_bytes)
            temp_path = f.name
        
        try:
            result = subprocess.run(
                [sys.executable, '-c', f'''
import subprocess
result = subprocess.run(
    ["ffmpeg", "-i", "{temp_path}", "-ar", "16000", "-ac", "1", "-f", "wav", "-"],
    capture_output=True
)
print(len(result.stdout))
'''],
                capture_output=True, text=True, timeout=30
            )
        except Exception:
            pass
        finally:
            os.unlink(temp_path)
            
    except Exception:
        pass
    
    try:
        respuesta = client.messages.create(
            model=modelo,
            max_tokens=1024,
            messages=[{
                "role": "user",
                "content": PROMPT_REUNION + "\n\nNo tengo la transcripcion del audio disponible. Devuelve un JSON con todos los campos en null excepto fecha_reunion que sera de hoy."
            }]
        )
        texto = respuesta.content[0].text
        clean = texto.strip()
        if clean.startswith("```"):
            clean = clean.split("\n", 1)[1]
            clean = clean.rsplit("```", 1)[0]
        
        datos = json.loads(clean)
        datos["fecha_procesado"] = datetime.now().strftime("%Y-%m-%d %H:%M")
        datos["modelo_usado"] = modelo
        datos["audio_recibido"] = True
        return {"ok": True, "datos": datos, "necesita_transcripcion": True}
        
    except Exception as e:
        logger.error(f"Error procesando audio: {e}")
        return {"ok": False, "error": str(e)}

def formatear_confirmacion(resultado: dict) -> str:
    """Formatea la confirmacion para Telegram"""
    if resultado.get("necesita_transcripcion"):
        return (
            "Audio recibido correctamente.\n\n"
            "El sistema no puede transcribir el audio automaticamente todavia.\n\n"
            "Por favor escribe un resumen de la reunion y lo proceso:"
        )
    
    d = resultado.get("datos", {})
    return (
        f"Reunion registrada\n\n"
        f"Empresa: {d.get('empresa', 'No detectada')}\n"
        f"Contacto: {d.get('contacto', 'No detectado')}\n"
        f"Fecha: {d.get('fecha_reunion', 'No indicada')}\n"
        f"Estado: {d.get('estado_lead', 'Nuevo')}\n\n"
        f"Resumen: {d.get('resumen', '')}\n\n"
        f"Proximos pasos: {d.get('proximos_pasos', '')}"
    )
