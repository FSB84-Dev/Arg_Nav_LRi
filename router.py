"""
ROUTER — Decide si una tarea va por ruta SIMPLE (Python puro) o COMPLEJA (Claude Agente)
"""

# Umbrales de decision
AUDIO_DURACION_MAXIMA_SIMPLE = 180  # 3 minutos en segundos
AUDIO_TAMANO_MAXIMO_SIMPLE = 5 * 1024 * 1024  # 5MB


def decidir_ruta_audio(duracion_segundos: int = 0, tamano_bytes: int = 0) -> str:
      """
          Decide si un audio va por ruta simple o compleja.

                  Ruta SIMPLE: audio corto y claro -> Claude Haiku (rapido, barato)
                      Ruta COMPLEJA: audio largo o dudoso -> Claude Sonnet (inteligente)

                              Returns: "simple" o "complejo"
      """
      if duracion_segundos > AUDIO_DURACION_MAXIMA_SIMPLE:
                return "complejo"

      if tamano_bytes > AUDIO_TAMANO_MAXIMO_SIMPLE:
                return "complejo"

      return "simple"


def decidir_ruta_licitacion(importe_euros: float = 0) -> str:
      """
          Decide si una licitacion merece analisis profundo.

                  Ruta SIMPLE: licitacion pequena -> resumen basico
                      Ruta COMPLEJA: licitacion grande -> analisis Claude completo

                              Returns: "simple" o "complejo"
      """
      if importe_euros >= 100000:
                return "complejo"

      return "simple"


def decidir_ruta_empresa(empleados: int = 0, tiene_licitaciones: bool = False) -> str:
      """
          Decide si una empresa merece perfil detallado.

                  Ruta SIMPLE: empresa pequena -> datos basicos
                      Ruta COMPLEJA: empresa grande o activa en licitaciones -> perfil completo

                              Returns: "simple" o "complejo"
      """
      if empleados >= 20 or tiene_licitaciones:
                return "complejo"

      return "simple"
  
